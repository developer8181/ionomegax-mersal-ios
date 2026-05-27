"""Extreme Site Server — offline branch cache and upstream synchronization."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from epms.security import AGENT_TOKEN_HEADER
from epms.storage import Database

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CACHE_DB = PROJECT_ROOT / "data" / f"site-{os.environ.get('EPMS_SITE_ID', 'local')}.sqlite3"


def _request_json(url: str, *, method: str = "GET", payload: dict | None = None, token: str = "") -> dict:
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers[AGENT_TOKEN_HEADER] = token
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"upstream HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"upstream unreachable: {exc.reason}") from exc


def heartbeat(args: argparse.Namespace) -> dict:
    payload = {
        "agent_id": args.agent_id,
        "agent_type": "site-server",
        "hostname": args.hostname,
        "os_name": args.os_name,
        "version": args.version,
        "metadata": {
            "site_id": args.site_id,
            "upstream": args.upstream,
            "offline_cache": str(args.cache_db),
        },
    }
    return _request_json(
        f"{args.upstream.rstrip('/')}/api/agents/heartbeat",
        method="POST",
        payload=payload,
        token=args.agent_token,
    )


def cache_status(args: argparse.Namespace) -> dict:
    db = Database(args.cache_db)
    db.init_schema()
    return {
        "cache_db": str(args.cache_db),
        "users": len(db.list_users()),
        "printers": len(db.list_printers()),
        "jobs": len(db.list_jobs()),
        "pending_sync": len(db.list_site_outbox(site_id=args.site_id, pending_only=True)),
    }


def enqueue_job(args: argparse.Namespace) -> dict:
    db = Database(args.cache_db)
    db.init_schema()
    job = db.submit_job(
        user_id=args.user_id,
        printer_id=args.printer_id,
        document_name=args.document,
        pages=args.pages,
        copies=args.copies,
        color=args.color,
        duplex=args.duplex,
        account=args.account,
        source="site-server",
        agent_id=args.agent_id,
    )
    outbox = db.enqueue_site_sync(
        site_id=args.site_id,
        method="POST",
        path="/api/jobs",
        payload={
            "user_id": args.user_id,
            "printer_id": args.printer_id,
            "document_name": args.document,
            "pages": args.pages,
            "copies": args.copies,
            "color": args.color,
            "duplex": args.duplex,
            "account": args.account,
            "source": "site-server",
            "agent_id": args.agent_id,
        },
    )
    return {"cached_job": job, "outbox": outbox}


def sync_outbox(args: argparse.Namespace) -> dict:
    db = Database(args.cache_db)
    db.init_schema()
    pending = db.list_site_outbox(site_id=args.site_id, pending_only=True)
    results = []
    for item in pending:
        url = f"{args.upstream.rstrip('/')}{item['path']}"
        try:
            response = _request_json(
                url,
                method=item["method"],
                payload=item["payload"],
                token=args.agent_token,
            )
            db.mark_site_outbox_synced(int(item["id"]))
            results.append({"id": item["id"], "status": "synced", "response": response})
        except RuntimeError as exc:
            results.append({"id": item["id"], "status": "failed", "error": str(exc)})
            if args.stop_on_error:
                break
    return {"processed": len(results), "results": results}


def pull_snapshot(args: argparse.Namespace) -> dict:
    db = Database(args.cache_db)
    db.init_schema()
    users = _request_json(f"{args.upstream.rstrip('/')}/api/users", token=args.agent_token)
    printers = _request_json(f"{args.upstream.rstrip('/')}/api/printers", token=args.agent_token)
    db.set_setting("upstream_snapshot", {"users": users, "printers": printers})
    return {"users": len(users), "printers": len(printers), "cached_at": "local"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme Site Server")
    parser.add_argument("--site-id", default=os.environ.get("EPMS_SITE_ID", "site-local"))
    parser.add_argument("--upstream", default=os.environ.get("EPMS_UPSTREAM_URL", "http://127.0.0.1:8080"))
    parser.add_argument("--agent-id", default="site-server-local")
    parser.add_argument("--agent-token", default=os.environ.get("EPMS_AGENT_TOKEN", ""))
    parser.add_argument("--cache-db", type=Path, default=DEFAULT_CACHE_DB)
    parser.add_argument("--hostname", default=os.environ.get("HOSTNAME", "site-server"))
    parser.add_argument("--os-name", default="Linux")
    parser.add_argument("--version", default="1.0.0")
    sub = parser.add_subparsers(dest="command", required=True)

    hb = sub.add_parser("heartbeat", help="Register site server with upstream")
    hb.set_defaults(func=heartbeat)

    status = sub.add_parser("status", help="Show local cache status")
    status.set_defaults(func=cache_status)

    cache = sub.add_parser("cache-job", help="Store job locally and queue upstream sync")
    cache.add_argument("--user-id", type=int, required=True)
    cache.add_argument("--printer-id", type=int, required=True)
    cache.add_argument("--document", required=True)
    cache.add_argument("--pages", type=int, required=True)
    cache.add_argument("--copies", type=int, default=1)
    cache.add_argument("--account", default="Branch")
    cache.add_argument("--color", action="store_true")
    cache.add_argument("--duplex", action="store_true")
    cache.set_defaults(func=enqueue_job)

    sync = sub.add_parser("sync", help="Push pending outbox events to upstream")
    sync.add_argument("--stop-on-error", action="store_true")
    sync.set_defaults(func=sync_outbox)

    pull = sub.add_parser("pull-snapshot", help="Pull users/printers snapshot from upstream")
    pull.set_defaults(func=pull_snapshot)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(args.func(args), indent=2, ensure_ascii=False))
        return 0
    except (RuntimeError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

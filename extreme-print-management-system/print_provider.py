"""Extreme Print Provider prototype.

This CLI represents the component installed on a Windows Print Server, Linux
CUPS host, macOS print host, or local gateway. It turns spooler events into
Extreme Server job submissions and keeps an offline queue when the server cannot
be reached.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from epms.agents import build_heartbeat
from epms.cups_provider import SeenJobStore, cups_job_to_spool_event, discover_cups_printers, list_cups_jobs
from epms.print_provider import OfflineQueue, parse_spool_event
from epms.security import AGENT_TOKEN_HEADER

DEFAULT_QUEUE = Path(__file__).resolve().parent / "data" / "print-provider-offline.jsonl"
DEFAULT_CUPS_STATE = Path(__file__).resolve().parent / "data" / "cups-seen-jobs.json"


def request_json(server_url: str, path: str, payload: dict | None = None, agent_token: str = "") -> object:
    url = server_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if agent_token:
        headers[AGENT_TOKEN_HEADER] = agent_token
    request = Request(url, data=data, headers=headers)
    if payload is not None:
        request.method = "POST"
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{exc.code} {exc.reason}: {body}") from exc
    except URLError as exc:
        raise RuntimeError(f"server unavailable: {exc.reason}") from exc


def send_heartbeat(args: argparse.Namespace) -> object:
    heartbeat = build_heartbeat(
        agent_id=args.agent_id,
        agent_type="print-provider",
        metadata={
            "mode": "print-provider",
            "spooler": args.spooler,
            "queues": [queue.strip() for queue in args.queue_name.split(",") if queue.strip()],
        },
    )
    return request_json(args.server, "/api/agents/heartbeat", heartbeat.to_dict(), args.agent_token)


def submit_event(args: argparse.Namespace) -> object:
    event = parse_spool_event(
        {
            "user_id": args.user_id,
            "printer_id": args.printer_id,
            "document_name": args.document,
            "pages": args.pages,
            "copies": args.copies,
            "color": args.color,
            "duplex": args.duplex,
            "account": args.account,
            "spool_id": args.spool_id,
        },
        default_agent_id=args.agent_id,
    )
    payload = event.to_job_payload()
    try:
        return request_json(args.server, "/api/jobs", payload, args.agent_token)
    except RuntimeError:
        if not args.offline_queue:
            raise
        queue = OfflineQueue(args.offline_queue)
        queue.enqueue(payload)
        return {"queued": True, "queue_path": str(args.offline_queue), "pending": queue.count(), "payload": payload}


def submit_event_file(args: argparse.Namespace) -> object:
    with Path(args.file).open("r", encoding="utf-8") as handle:
        event_data = json.load(handle)
    event = parse_spool_event(event_data, default_agent_id=args.agent_id)
    payload = event.to_job_payload()
    try:
        return request_json(args.server, "/api/jobs", payload, args.agent_token)
    except RuntimeError:
        if not args.offline_queue:
            raise
        queue = OfflineQueue(args.offline_queue)
        queue.enqueue(payload)
        return {"queued": True, "queue_path": str(args.offline_queue), "pending": queue.count(), "payload": payload}


def flush_queue(args: argparse.Namespace) -> object:
    queue = OfflineQueue(args.offline_queue)
    remaining = []
    submitted = []
    for payload in queue.read_all():
        try:
            submitted.append(request_json(args.server, "/api/jobs", payload, args.agent_token))
        except RuntimeError:
            remaining.append(payload)
    queue.replace(remaining)
    return {"submitted": submitted, "remaining": len(remaining)}


def queue_status(args: argparse.Namespace) -> object:
    queue = OfflineQueue(args.offline_queue)
    return {"queue_path": str(args.offline_queue), "pending": queue.count()}


def cups_discover(_: argparse.Namespace) -> object:
    return [printer.to_dict() for printer in discover_cups_printers()]


def load_json_mapping(path: Path) -> dict[str, int]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return {str(key): int(value) for key, value in data.items()}


def submit_payload_or_queue(args: argparse.Namespace, payload: dict) -> dict:
    try:
        return {"submitted": request_json(args.server, "/api/jobs", payload, args.agent_token)}
    except RuntimeError:
        queue = OfflineQueue(args.offline_queue)
        queue.enqueue(payload)
        return {"queued": True, "pending": queue.count(), "payload": payload}


def cups_poll(args: argparse.Namespace) -> object:
    user_map = load_json_mapping(args.user_map)
    printer_map = load_json_mapping(args.printer_map)
    seen_store = SeenJobStore(args.cups_state)
    seen_jobs = seen_store.read()
    results = []

    for cups_job in list_cups_jobs():
        if cups_job.job_ref in seen_jobs:
            continue
        event = cups_job_to_spool_event(
            cups_job,
            user_map=user_map,
            printer_map=printer_map,
            default_pages=args.default_pages,
            account=args.account,
            agent_id=args.agent_id,
        )
        results.append(submit_payload_or_queue(args, event.to_job_payload()))
        seen_jobs.add(cups_job.job_ref)

    seen_store.write(seen_jobs)
    return {"processed": len(results), "results": results, "seen_state": str(args.cups_state)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme Print Provider prototype")
    parser.add_argument("--server", default="http://127.0.0.1:8080", help="Extreme Server URL")
    parser.add_argument("--agent-id", default="print-provider-local", help="Stable print provider agent id")
    parser.add_argument("--agent-token", default=os.environ.get("EPMS_AGENT_TOKEN", ""), help="Agent API token")
    parser.add_argument("--offline-queue", type=Path, default=DEFAULT_QUEUE, help="Local JSONL queue for offline jobs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    heartbeat = subparsers.add_parser("heartbeat", help="Register or refresh this print provider")
    heartbeat.add_argument("--spooler", default="cups", choices=["cups", "windows-spooler", "macos", "gateway"])
    heartbeat.add_argument("--queue-name", default="default", help="Comma-separated local queue names")
    heartbeat.set_defaults(func=send_heartbeat)

    submit = subparsers.add_parser("submit-event", help="Submit one spooler event to the server")
    submit.add_argument("--user-id", type=int, required=True)
    submit.add_argument("--printer-id", type=int, required=True)
    submit.add_argument("--document", required=True)
    submit.add_argument("--pages", type=int, required=True)
    submit.add_argument("--copies", type=int, default=1)
    submit.add_argument("--account", default="Personal")
    submit.add_argument("--color", action="store_true")
    submit.add_argument("--duplex", action="store_true")
    submit.add_argument("--spool-id", default="")
    submit.set_defaults(func=submit_event)

    submit_file = subparsers.add_parser("submit-file", help="Submit one JSON spooler event file")
    submit_file.add_argument("file")
    submit_file.set_defaults(func=submit_event_file)

    flush = subparsers.add_parser("flush-queue", help="Replay queued offline events")
    flush.set_defaults(func=flush_queue)

    status = subparsers.add_parser("queue-status", help="Show offline queue status")
    status.set_defaults(func=queue_status)

    cups_discover_parser = subparsers.add_parser("cups-discover", help="Discover real CUPS printers using lpstat")
    cups_discover_parser.set_defaults(func=cups_discover)

    cups = subparsers.add_parser("cups-poll", help="Poll real CUPS jobs and submit new jobs to Extreme Server")
    cups.add_argument("--user-map", type=Path, required=True, help="JSON map of CUPS usernames to Extreme user IDs")
    cups.add_argument("--printer-map", type=Path, required=True, help="JSON map of CUPS queue names to Extreme printer IDs")
    cups.add_argument("--cups-state", type=Path, default=DEFAULT_CUPS_STATE, help="State file of already-seen CUPS jobs")
    cups.add_argument("--default-pages", type=int, default=1, help="Fallback page count when CUPS does not expose pages")
    cups.add_argument("--account", default="CUPS")
    cups.set_defaults(func=cups_poll)

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

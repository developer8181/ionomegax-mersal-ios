"""Extreme Client Agent prototype.

This CLI stands in for the workstation component. In production this becomes a
native Windows/macOS/Linux service that monitors local/direct print queues.
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from epms.agents import build_heartbeat


def request_json(server_url: str, path: str, payload: dict | None = None) -> object:
    url = server_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    if payload is not None:
        request.method = "POST"
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{exc.code} {exc.reason}: {body}") from exc


def find_user(server_url: str, user_ref: str) -> dict:
    users = request_json(server_url, "/api/users")
    for user in users:
        if str(user["id"]) == user_ref or user["username"] == user_ref:
            return user
    raise RuntimeError(f"user not found: {user_ref}")


def send_heartbeat(args: argparse.Namespace) -> object:
    heartbeat = build_heartbeat(
        agent_id=args.agent_id,
        agent_type="client",
        metadata={"mode": "client-agent", "direct_print_monitor": args.direct_monitor},
    )
    return request_json(args.server, "/api/agents/heartbeat", heartbeat.to_dict())


def show_balance(args: argparse.Namespace) -> object:
    user = find_user(args.server, args.user)
    return {
        "username": user["username"],
        "display_name": user["display_name"],
        "department": user["department"],
        "balance_cents": user["balance_cents"],
        "monthly_quota_cents": user["monthly_quota_cents"],
    }


def submit_job(args: argparse.Namespace) -> object:
    user = find_user(args.server, args.user)
    payload = {
        "user_id": user["id"],
        "printer_id": args.printer_id,
        "document_name": args.document,
        "pages": args.pages,
        "copies": args.copies,
        "color": args.color,
        "duplex": args.duplex,
        "account": args.account,
        "source": "client-agent",
        "agent_id": args.agent_id,
    }
    return request_json(args.server, "/api/jobs", payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme Client Agent prototype")
    parser.add_argument("--server", default="http://127.0.0.1:8080", help="Extreme Server URL")
    parser.add_argument("--agent-id", default="client-agent-local", help="Stable client agent id")
    subparsers = parser.add_subparsers(dest="command", required=True)

    heartbeat = subparsers.add_parser("heartbeat", help="Register or refresh this client agent")
    heartbeat.add_argument("--direct-monitor", action="store_true", help="Mark this client as a direct print monitor")
    heartbeat.set_defaults(func=send_heartbeat)

    balance = subparsers.add_parser("balance", help="Show a user's print balance")
    balance.add_argument("--user", required=True, help="Username or numeric user id")
    balance.set_defaults(func=show_balance)

    submit = subparsers.add_parser("submit-job", help="Submit a simulated workstation print job")
    submit.add_argument("--user", required=True, help="Username or numeric user id")
    submit.add_argument("--printer-id", type=int, required=True)
    submit.add_argument("--document", required=True)
    submit.add_argument("--pages", type=int, required=True)
    submit.add_argument("--copies", type=int, default=1)
    submit.add_argument("--account", default="Personal")
    submit.add_argument("--color", action="store_true")
    submit.add_argument("--duplex", action="store_true")
    submit.set_defaults(func=submit_job)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(args.func(args), indent=2, ensure_ascii=False))
        return 0
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

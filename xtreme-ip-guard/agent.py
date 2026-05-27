"""CLI prototype for an Xtreme IP Guard endpoint agent."""

from __future__ import annotations

import argparse
import json
import platform
import socket
import sys
import urllib.error
import urllib.request
from typing import Any

from xig import __version__


DEFAULT_SERVER = "http://127.0.0.1:8090"


def post_json(server: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{server.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310 - local prototype URL supplied by operator
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"server returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"could not reach Xtreme IP Guard server: {exc}") from exc


def heartbeat(args: argparse.Namespace) -> None:
    hostname = args.hostname or socket.gethostname()
    endpoint_id = args.endpoint_id or hostname
    payload = {
        "agent_id": args.agent_id or f"xig-agent-{endpoint_id}",
        "agent_type": "endpoint",
        "hostname": hostname,
        "os_name": args.os_name or platform.platform(),
        "version": __version__,
        "metadata": {
            "endpoint_id": endpoint_id,
            "owner": args.owner,
            "site": args.site,
            "capabilities": ["heartbeat", "telemetry", "policy-preview"],
        },
    }
    print(json.dumps(post_json(args.server, "/api/agents/heartbeat", payload), indent=2, ensure_ascii=False))


def simulate_event(args: argparse.Namespace) -> None:
    payload = {
        "endpoint_id": args.endpoint_id,
        "actor": args.actor,
        "event_type": args.event_type,
        "channel": args.channel,
        "resource": args.resource,
        "classification": args.classification,
        "destination": args.destination,
        "process": args.process,
        "severity": args.severity,
        "behavior_flags": args.behavior_flag,
        "metadata": {"source": "agent-cli-prototype"},
    }
    print(json.dumps(post_json(args.server, "/api/events", payload), indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Xtreme IP Guard endpoint agent prototype")
    parser.add_argument("--server", default=DEFAULT_SERVER, help=f"Xtreme IP Guard server URL, default: {DEFAULT_SERVER}")

    subcommands = parser.add_subparsers(dest="command", required=True)

    heartbeat_parser = subcommands.add_parser("heartbeat", help="Register or refresh an endpoint agent")
    heartbeat_parser.add_argument("--agent-id", default="")
    heartbeat_parser.add_argument("--endpoint-id", default="")
    heartbeat_parser.add_argument("--hostname", default="")
    heartbeat_parser.add_argument("--os-name", default="")
    heartbeat_parser.add_argument("--owner", default="")
    heartbeat_parser.add_argument("--site", default="HQ")
    heartbeat_parser.set_defaults(func=heartbeat)

    event_parser = subcommands.add_parser("simulate-event", help="Send a defensive telemetry event")
    event_parser.add_argument("--endpoint-id", required=True)
    event_parser.add_argument("--actor", required=True)
    event_parser.add_argument("--event-type", default="file_copy")
    event_parser.add_argument("--channel", default="removable_media")
    event_parser.add_argument("--resource", required=True)
    event_parser.add_argument("--classification", default="internal")
    event_parser.add_argument("--destination", default="")
    event_parser.add_argument("--process", default="")
    event_parser.add_argument("--severity", type=int, default=25)
    event_parser.add_argument("--behavior-flag", action="append", default=[])
    event_parser.set_defaults(func=simulate_event)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

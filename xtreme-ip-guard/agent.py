"""Ionomegax Mersal Guard — endpoint agent CLI and daemon."""

from __future__ import annotations

import argparse
import json
import platform
import socket
import sys
from pathlib import Path

from xig import __version__
from xig.agent_runtime import AgentConfig, MersalAgent
from xig.brand import BRAND
from xig.enforcement import LocalEnforcer
from xig.platform import collect_profile, collect_sensor_events

DEFAULT_SERVER = "http://127.0.0.1:8090"
DEFAULT_CONFIG = Path(__file__).resolve().parent / "config" / "agent.json"


def post_json(server: str, path: str, payload: dict, *, token: str = "") -> dict:
    import urllib.error
    import urllib.request

    headers = {"Content-Type": "application/json", "User-Agent": f"MersalAgent/{__version__}"}
    if token:
        headers["X-Mersal-Token"] = token
    request = urllib.request.Request(
        f"{server.rstrip('/')}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"server returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"could not reach Mersal Guard server: {exc}") from exc


def heartbeat(args: argparse.Namespace) -> None:
    hostname = args.hostname or socket.gethostname()
    endpoint_id = args.endpoint_id or hostname
    profile = collect_profile()
    payload = {
        "agent_id": args.agent_id or f"mersal-agent-{endpoint_id}",
        "agent_type": "endpoint",
        "hostname": hostname,
        "os_name": args.os_name or profile.os_name,
        "version": __version__,
        "metadata": {
            "endpoint_id": endpoint_id,
            "owner": args.owner,
            "site": args.site,
            "brand": BRAND["full_name"],
            "platform_id": profile.platform_id,
            "capabilities": list(profile.capabilities),
            "security_features": profile.security_features,
            "sensors": profile.sensors,
        },
    }
    print(json.dumps(post_json(args.server, "/api/agents/heartbeat", payload, token=args.token), indent=2, ensure_ascii=False))


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
        "metadata": {"source": "mersal-agent-cli"},
    }
    print(json.dumps(post_json(args.server, "/api/events", payload, token=args.token), indent=2, ensure_ascii=False))


def run_daemon(args: argparse.Namespace) -> None:
    config_path = Path(args.config)
    if not config_path.is_file():
        raise SystemExit(f"config not found: {config_path}")
    MersalAgent(AgentConfig.load(config_path)).run_forever()


def show_profile(_: argparse.Namespace) -> None:
    profile = collect_profile()
    print(json.dumps(profile.__dict__, indent=2, ensure_ascii=False, default=list))


def show_sensors(_: argparse.Namespace) -> None:
    events = collect_sensor_events()
    print(json.dumps([event.__dict__ for event in events], indent=2, ensure_ascii=False, default=list))


def show_status(args: argparse.Namespace) -> None:
    state_dir = Path(args.state_dir)
    state = LocalEnforcer(state_dir).load()
    print(json.dumps({"platform": platform.platform(), "state": state.to_dict()}, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=BRAND["agent_name"])
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--token", default="")

    subcommands = parser.add_subparsers(dest="command", required=True)

    daemon_parser = subcommands.add_parser("daemon", help="Run continuous agent (heartbeat + sensors + enforcement)")
    daemon_parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    daemon_parser.set_defaults(func=run_daemon)

    heartbeat_parser = subcommands.add_parser("heartbeat", help="Send one heartbeat")
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

    subcommands.add_parser("profile", help="Show OS profile and capabilities").set_defaults(func=show_profile)
    subcommands.add_parser("sensors", help="List live sensor events from this host").set_defaults(func=show_sensors)

    status_parser = subcommands.add_parser("status", help="Show local enforcement state")
    status_parser.add_argument("--state-dir", default=str(Path.home() / ".mersal-guard"))
    status_parser.set_defaults(func=show_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

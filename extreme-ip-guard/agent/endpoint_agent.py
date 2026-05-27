"""Reference endpoint-agent CLI for Extreme IP Guard.

This binary mirrors the behaviour of a production XIG agent at the protocol
level. It can:

* enrol against the control plane using a one-time token,
* send heartbeats,
* emit simulated telemetry events from any of the sensors in
  :mod:`agent.sensors`,
* poll for and complete response commands queued by the SOAR-lite engine.

Run ``python -m agent.endpoint_agent --help`` for the full list of
sub-commands.
"""

from __future__ import annotations

import argparse
import getpass
import json
import platform
import socket
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Allow running as a script from the repo root without installing the package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.sensors import ALL_SIMULATORS, SensorContext, simulator_names
from xig.core import utc_now_iso


DEFAULT_SERVER = "http://127.0.0.1:8090"
STATE_FILE = PROJECT_ROOT / "data" / "agent-state.json"


@dataclass
class AgentState:
    agent_id: str
    agent_secret: str
    server: str

    def save(self, path: Path = STATE_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path = STATE_FILE) -> "AgentState | None":
        if not path.exists():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(**raw)


def hw_fingerprint() -> str:
    """A deterministic-ish hardware fingerprint for the reference agent.

    A real agent would combine the CPU UUID, motherboard serial, and the
    first MAC address. Here we synthesise a stable value from the hostname
    and platform string so simulations stay reproducible.
    """

    raw = f"{platform.node()}|{platform.platform()}|{uuid.getnode()}"
    return f"hwfp-{abs(hash(raw)) & 0xFFFFFFFF:08x}"


def http_post(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"server returned {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"could not reach server: {exc.reason}")


def http_get(url: str) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"server returned {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"could not reach server: {exc.reason}")


# ---- CLI commands ----

def cmd_enrol(args: argparse.Namespace) -> int:
    agent_id = args.agent_id or f"agent-{socket.gethostname().lower()}-{uuid.uuid4().hex[:6]}"
    payload = {
        "enrol_token": args.token,
        "agent_id": agent_id,
        "hw_fp": hw_fingerprint(),
        "os_name": f"{platform.system()} {platform.release()}",
        "version": "0.1.0-ref",
    }
    response = http_post(f"{args.server}/api/agents/enrol", payload)
    state = AgentState(
        agent_id=response["agent_id"],
        agent_secret=response["agent_secret"],
        server=args.server,
    )
    state.save()
    print(f"Enrolled as {state.agent_id}.")
    print(f"Policy bundle v{response['policy_bundle'].get('version')} cached.")
    return 0


def cmd_heartbeat(args: argparse.Namespace) -> int:
    state = require_state(args)
    payload = {"agent_id": state.agent_id, "version": "0.1.0-ref"}
    response = http_post(f"{state.server}/api/agents/heartbeat", payload)
    print(json.dumps(response, indent=2))
    return 0


def cmd_emit(args: argparse.Namespace) -> int:
    state = require_state(args)
    simulator = ALL_SIMULATORS.get(args.sensor)
    if simulator is None:
        print(f"unknown sensor '{args.sensor}'. Known: {', '.join(simulator_names())}", file=sys.stderr)
        return 2
    ctx = SensorContext(agent_id=state.agent_id, user=args.user or getpass.getuser())
    event = simulator(ctx)
    payload = event.to_dict()
    if args.user:
        payload["user_id"] = args.user
    response = http_post(f"{state.server}/api/events", payload)
    print(json.dumps(response, indent=2, ensure_ascii=False))
    return 0


def cmd_poll(args: argparse.Namespace) -> int:
    state = require_state(args)
    response = http_get(f"{state.server}/api/agents/poll?agent_id={state.agent_id}")
    if not response:
        print("(no commands pending)")
        return 0
    for command in response:
        print(json.dumps(command, indent=2, ensure_ascii=False))
        if args.complete:
            result = http_post(
                f"{state.server}/api/commands/complete",
                {
                    "command_uid": command["command_uid"],
                    "status": "succeeded",
                    "result": {"executed_at": utc_now_iso(), "playbook": command["playbook"]},
                    "actor": f"agent:{state.agent_id}",
                },
            )
            print(f"  -> completed {result['command_uid']}")
    return 0


def cmd_storm(args: argparse.Namespace) -> int:
    """Fire a representative sequence of events to populate the dashboard."""

    state = require_state(args)
    ctx = SensorContext(agent_id=state.agent_id, user=args.user or "sara")
    sequence = ["usb_attach", "usb_mass_copy", "office_shell", "c2_callout", "auth_brute_force", "dlp_match", "clipboard_secret"]
    for name in sequence:
        event = ALL_SIMULATORS[name](ctx)
        response = http_post(f"{state.server}/api/events", event.to_dict())
        alerts = response.get("alerts", [])
        if alerts:
            for alert in alerts:
                print(f"  ALERT [{alert['severity'].upper():8}] {alert['title']} ({alert['rule_id']})")
        else:
            print(f"  event {name}: no alerts")
        time.sleep(args.delay)
    return 0


def require_state(args: argparse.Namespace) -> AgentState:
    state = AgentState.load()
    if state is None:
        print("agent is not enrolled. Run 'enrol --token <one-time-token>' first.", file=sys.stderr)
        sys.exit(2)
    if args.server and args.server != state.server:
        state.server = args.server
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme IP Guard reference endpoint agent")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Base URL of the XIG control plane")

    sub = parser.add_subparsers(dest="command", required=True)

    enrol = sub.add_parser("enrol", help="Enrol this host using a one-time token")
    enrol.add_argument("--token", required=True, help="One-time enrolment token from the console")
    enrol.add_argument("--agent-id", help="Override the auto-generated agent id")
    enrol.set_defaults(func=cmd_enrol)

    hb = sub.add_parser("heartbeat", help="Send a heartbeat")
    hb.set_defaults(func=cmd_heartbeat)

    emit = sub.add_parser("emit", help="Emit a simulated sensor event")
    emit.add_argument("sensor", choices=sorted(simulator_names()))
    emit.add_argument("--user", help="Console user id to associate with the event")
    emit.set_defaults(func=cmd_emit)

    poll = sub.add_parser("poll", help="Fetch and (optionally) complete queued commands")
    poll.add_argument("--complete", action="store_true", help="Mark fetched commands as succeeded")
    poll.set_defaults(func=cmd_poll)

    storm = sub.add_parser("storm", help="Run a deterministic attack-storm simulation")
    storm.add_argument("--user", help="Pretend the events belong to this console user", default="sara")
    storm.add_argument("--delay", type=float, default=0.2, help="Seconds between events")
    storm.set_defaults(func=cmd_storm)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

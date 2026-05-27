"""CLI prototype for Extreme IP Guard sensors and edge enforcers."""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request

from xipg.agents import build_heartbeat, supported_control_profiles


DEFAULT_BASE_URL = os.environ.get("XIPG_URL", "http://127.0.0.1:8090")


def api_request(path: str, payload: dict | None = None, method: str = "GET") -> dict:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(f"{DEFAULT_BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            data = json.loads(body)
        except json.JSONDecodeError as error:
            raise RuntimeError(body or str(exc)) from error
        raise RuntimeError(data.get("error") or str(exc)) from exc


def command_profiles(_: argparse.Namespace) -> None:
    print(json.dumps(supported_control_profiles(), indent=2))


def command_heartbeat(args: argparse.Namespace) -> None:
    heartbeat = build_heartbeat(
        agent_id=args.agent_id,
        agent_type=args.agent_type,
        version=args.version,
        metadata={
            "control_profile": args.control_profile,
            "segment": args.segment,
            "enforcement_mode": args.enforcement_mode,
        },
    )
    response = api_request("/api/agents/heartbeat", payload=heartbeat.to_dict(), method="POST")
    print(json.dumps(response, indent=2))


def command_simulate_event(args: argparse.Namespace) -> None:
    payload = {
        "asset_id": args.asset_id,
        "source_ip": args.source_ip,
        "destination_ip": args.destination_ip,
        "destination_port": args.destination_port,
        "protocol": args.protocol,
        "country": args.country,
        "bytes_out": args.bytes_out,
        "bytes_in": args.bytes_in,
        "process_name": args.process_name,
        "ip_reputation_score": args.ip_reputation_score,
        "tor_exit_node": args.tor_exit_node,
        "geo_anomaly": args.geo_anomaly,
        "burst_connections": args.burst_connections,
    }
    response = api_request("/api/events", payload=payload, method="POST")
    print(json.dumps(response, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme IP Guard sensor prototype")
    subparsers = parser.add_subparsers(dest="command", required=True)

    profiles = subparsers.add_parser("profiles", help="List supported control profiles")
    profiles.set_defaults(func=command_profiles)

    heartbeat = subparsers.add_parser("heartbeat", help="Send a sensor heartbeat")
    heartbeat.add_argument("--agent-id", required=True)
    heartbeat.add_argument("--agent-type", default="sensor", choices=["sensor", "edge-enforcer", "site-relay", "deception-node"])
    heartbeat.add_argument("--version", default="0.1.0")
    heartbeat.add_argument("--control-profile", default="generic-gateway")
    heartbeat.add_argument("--segment", default="users")
    heartbeat.add_argument("--enforcement-mode", default="adaptive")
    heartbeat.set_defaults(func=command_heartbeat)

    simulate = subparsers.add_parser("simulate-event", help="Submit a simulated network event")
    simulate.add_argument("--asset-id", type=int, required=True)
    simulate.add_argument("--source-ip", default="10.10.20.17")
    simulate.add_argument("--destination-ip", required=True)
    simulate.add_argument("--destination-port", type=int, required=True)
    simulate.add_argument("--protocol", default="tcp")
    simulate.add_argument("--country", default="ZZ")
    simulate.add_argument("--bytes-out", type=int, default=0)
    simulate.add_argument("--bytes-in", type=int, default=0)
    simulate.add_argument("--process-name", default="")
    simulate.add_argument("--ip-reputation-score", type=int, default=0)
    simulate.add_argument("--tor-exit-node", action="store_true")
    simulate.add_argument("--geo-anomaly", action="store_true")
    simulate.add_argument("--burst-connections", type=int, default=0)
    simulate.set_defaults(func=command_simulate_event)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

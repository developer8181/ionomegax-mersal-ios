"""Extreme Edge Enforcer Agent — gateway/firewall enforcement prototype.

In production this becomes a Linux service using nftables/eBPF-XDP or
Windows WFP to apply signed policy bundles from Extreme IP Guard Server.
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from eipg.agents import build_heartbeat


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


def send_heartbeat(args: argparse.Namespace) -> object:
    heartbeat = build_heartbeat(
        agent_id=args.agent_id,
        agent_type="edge-enforcer",
        metadata={
            "mode": args.backend,
            "interfaces": args.interfaces.split(","),
            "rules_applied": args.simulate_rules,
        },
    )
    return request_json(args.server, "/api/agents/heartbeat", heartbeat.to_dict())


def pull_policy(args: argparse.Namespace) -> object:
    bundle = request_json(args.server, "/api/policy-bundle")
    rules_count = len(bundle.get("rules", []))
    blocks_count = len(bundle.get("blocks", []))
    print(f"[edge-enforcer] Policy v{bundle.get('version')} — {rules_count} rules, {blocks_count} blocks")
    print(f"[edge-enforcer] Signature: {bundle.get('signature', '')[:16]}...")
    if args.simulate_rules:
        for rule in bundle.get("rules", [])[:5]:
            print(f"  → {rule['action'].upper():12} {rule['name']} (priority {rule['priority']})")
        if rules_count > 5:
            print(f"  ... and {rules_count - 5} more rules")
    return bundle


def evaluate_traffic(args: argparse.Namespace) -> object:
    payload = {
        "source_ip": args.source_ip,
        "destination_ip": args.destination_ip,
        "destination_port": args.port,
        "protocol": args.protocol,
        "zone": args.zone,
    }
    if args.device_id:
        payload["device_id"] = args.device_id
    decision = request_json(args.server, "/api/evaluate", payload)
    action = "ALLOW" if decision.get("allowed") else "DROP"
    print(f"[edge-enforcer] {action} {args.source_ip} → {args.destination_ip}:{args.port}/{args.protocol}")
    print(f"  Reason: {decision.get('reason')}")
    return decision


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme Edge Enforcer Agent")
    parser.add_argument("--server", default="http://127.0.0.1:8090", help="Extreme IP Guard Server URL")
    parser.add_argument("--agent-id", default="edge-enforcer-local", help="Stable edge agent id")
    parser.add_argument("--backend", default="nftables", choices=["nftables", "ebpf-xdp", "iptables", "wfp"])
    parser.add_argument("--interfaces", default="eth0", help="Comma-separated network interfaces")
    parser.add_argument("--simulate-rules", action="store_true", help="Print rules that would be applied")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("heartbeat", help="Register edge enforcer with central server")

    pull = sub.add_parser("pull-policy", help="Fetch and verify signed policy bundle")
    pull.add_argument("--simulate-rules", action="store_true")

    ev = sub.add_parser("evaluate", help="Evaluate a traffic flow against central policy")
    ev.add_argument("--source-ip", required=True)
    ev.add_argument("--destination-ip", default="8.8.8.8")
    ev.add_argument("--port", type=int, default=443)
    ev.add_argument("--protocol", default="tcp")
    ev.add_argument("--zone", default="default")
    ev.add_argument("--device-id", default="")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "heartbeat":
            result = send_heartbeat(args)
        elif args.command == "pull-policy":
            result = pull_policy(args)
        elif args.command == "evaluate":
            result = evaluate_traffic(args)
        else:
            raise RuntimeError(f"unknown command: {args.command}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

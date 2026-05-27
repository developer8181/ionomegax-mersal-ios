"""Extreme Flow Sensor — network telemetry and anomaly detection prototype.

In production this ingests NetFlow/IPFIX, Zeek logs, Suricata alerts, or
cloud VPC flow logs and feeds the central threat engine.
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
        agent_type="flow-collector",
        metadata={"collector": args.collector, "sensors": args.sensors.split(",")},
    )
    return request_json(args.server, "/api/agents/heartbeat", heartbeat.to_dict())


def ingest_flow(args: argparse.Namespace) -> object:
    payload = {
        "source_ip": args.source_ip,
        "destination_ip": args.destination_ip,
        "destination_port": args.port,
        "protocol": args.protocol,
        "bytes_sent": args.bytes,
        "packets": args.packets,
    }
    result = request_json(args.server, "/api/flows", payload)
    decision = result.get("decision", {})
    action = "ALLOW" if decision.get("allowed") else "BLOCK"
    print(f"[flow-sensor] {action} flow {args.source_ip} → {args.destination_ip}:{args.port}")
    return result


def simulate_scan(args: argparse.Namespace) -> object:
    results = []
    for port in range(args.start_port, args.start_port + args.port_count):
        payload = {
            "source_ip": args.source_ip,
            "destination_ip": args.target_ip,
            "destination_port": port,
            "protocol": "tcp",
            "bytes_sent": 64,
            "packets": 1,
        }
        results.append(request_json(args.server, "/api/flows", payload))
    print(f"[flow-sensor] Simulated port scan: {args.port_count} probes from {args.source_ip}")
    return {"probes": len(results), "last_decision": results[-1].get("decision") if results else None}


def report_brute_force(args: argparse.Namespace) -> object:
    return request_json(
        args.server,
        "/api/brute-force",
        {
            "source_ip": args.source_ip,
            "target_service": args.service,
            "failed_attempts": args.attempts,
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme Flow Sensor")
    parser.add_argument("--server", default="http://127.0.0.1:8090")
    parser.add_argument("--agent-id", default="flow-sensor-local")
    parser.add_argument("--collector", default="netflow-v9")
    parser.add_argument("--sensors", default="zeek,suricata")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("heartbeat")

    flow = sub.add_parser("ingest", help="Ingest a single network flow")
    flow.add_argument("--source-ip", required=True)
    flow.add_argument("--destination-ip", required=True)
    flow.add_argument("--port", type=int, default=443)
    flow.add_argument("--protocol", default="tcp")
    flow.add_argument("--bytes", type=int, default=1024)
    flow.add_argument("--packets", type=int, default=10)

    scan = sub.add_parser("simulate-scan", help="Simulate port scan for threat detection demo")
    scan.add_argument("--source-ip", default="203.0.113.99")
    scan.add_argument("--target-ip", default="10.0.1.1")
    scan.add_argument("--start-port", type=int, default=20)
    scan.add_argument("--port-count", type=int, default=15)

    bf = sub.add_parser("brute-force", help="Report brute-force attempt")
    bf.add_argument("--source-ip", required=True)
    bf.add_argument("--service", default="ssh")
    bf.add_argument("--attempts", type=int, default=10)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        commands = {
            "heartbeat": send_heartbeat,
            "ingest": ingest_flow,
            "simulate-scan": simulate_scan,
            "brute-force": report_brute_force,
        }
        result = commands[args.command](args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

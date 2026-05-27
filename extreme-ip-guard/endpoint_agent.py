"""Extreme Endpoint Agent — workstation NAC/posture prototype.

In production this becomes a native service that registers device identity,
reports posture compliance (OS patch level, AV status, TPM attestation),
and enforces local policies (USB control, process monitoring).
"""

from __future__ import annotations

import argparse
import json
import platform
import socket
import sys
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from eipg.agents import build_heartbeat
from eipg.core import normalize_mac


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


def local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def pseudo_mac() -> str:
    node = uuid.getnode()
    raw = f"{node:012x}"
    return normalize_mac(":".join(raw[i : i + 2] for i in range(0, 12, 2)))


def register_device(args: argparse.Namespace) -> object:
    payload = {
        "device_id": args.device_id,
        "hostname": socket.gethostname(),
        "mac_address": pseudo_mac(),
        "ip_address": local_ip(),
        "zone": args.zone,
        "owner": args.owner,
        "device_type": args.device_type,
        "tags": args.tags.split(",") if args.tags else [],
    }
    return request_json(args.server, "/api/devices", payload)


def send_heartbeat(args: argparse.Namespace) -> object:
    heartbeat = build_heartbeat(
        agent_id=args.agent_id,
        agent_type="endpoint-agent",
        metadata={
            "device_id": args.device_id,
            "posture": {
                "os": platform.platform(),
                "python": platform.python_version(),
                "antivirus": "simulated-ok",
                "disk_encrypted": True,
                "firewall_enabled": True,
            },
            "peripherals": {"usb_policy": "deny-unknown"},
        },
    )
    return request_json(args.server, "/api/agents/heartbeat", heartbeat.to_dict())


def check_access(args: argparse.Namespace) -> object:
    payload = {
        "source_ip": local_ip(),
        "destination_ip": args.destination_ip,
        "destination_port": args.port,
        "protocol": args.protocol,
        "device_id": args.device_id,
        "zone": args.zone,
    }
    return request_json(args.server, "/api/evaluate", payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme Endpoint Agent")
    parser.add_argument("--server", default="http://127.0.0.1:8090")
    parser.add_argument("--agent-id", default="endpoint-agent-local")
    parser.add_argument("--device-id", default="dev-endpoint-local")
    parser.add_argument("--zone", default="default")
    parser.add_argument("--owner", default="")
    parser.add_argument("--device-type", default="workstation")
    parser.add_argument("--tags", default="")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("register", help="Register this endpoint with the server")
    sub.add_parser("heartbeat", help="Send posture heartbeat")

    check = sub.add_parser("check-access", help="Verify network access for a destination")
    check.add_argument("--destination-ip", default="8.8.8.8")
    check.add_argument("--port", type=int, default=443)
    check.add_argument("--protocol", default="tcp")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "register":
            result = register_device(args)
        elif args.command == "heartbeat":
            result = send_heartbeat(args)
        elif args.command == "check-access":
            result = check_access(args)
            status = "ALLOWED" if result.get("allowed") else "DENIED"
            print(f"[endpoint-agent] Access {status}: {result.get('reason')}")
        else:
            raise RuntimeError(f"unknown command: {args.command}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Extreme IP Guard endpoint-agent prototype.

This CLI sends explicit, user-visible telemetry to a local Extreme IP Guard
server. It is a safe simulation layer for asset posture and DLP decisions, not a
stealth monitoring service.
"""

from __future__ import annotations

import argparse
import json
import platform
import socket
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


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
    hostname = args.hostname or socket.gethostname()
    payload = {
        "asset_id": args.asset_id,
        "hostname": hostname,
        "owner": args.owner,
        "department": args.department,
        "ip_address": args.ip_address,
        "os_name": args.os_name or platform.platform(),
        "agent_version": "0.1.0",
        "posture": {
            "encryption_enabled": not args.encryption_disabled,
            "edr_enabled": not args.edr_disabled,
            "firewall_enabled": not args.firewall_disabled,
            "os_patch_age_days": args.patch_age_days,
            "critical_vulns": args.critical_vulns,
            "high_vulns": args.high_vulns,
            "failed_login_count": args.failed_logins,
            "dlp_incidents_24h": args.dlp_incidents,
            "external_ip_exposure": args.external_exposure,
            "sensitive_data_at_rest": args.sensitive_data,
            "unusual_egress_mb": args.unusual_egress_mb,
        },
        "metadata": {
            "collection_mode": "transparent_cli",
            "notice": "prototype telemetry submitted by an operator",
        },
    }
    return request_json(args.server, "/api/assets/heartbeat", payload)


def send_dlp_event(args: argparse.Namespace) -> object:
    payload = {
        "asset_ref": args.asset_ref,
        "username": args.username,
        "channel": args.channel,
        "sensitivity": args.sensitivity,
        "destination": args.destination,
        "destination_trusted": args.destination_trusted,
        "bytes_count": args.bytes_count,
        "encrypted": args.encrypted,
        "user_override": args.user_override,
    }
    return request_json(args.server, "/api/dlp-events", payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme IP Guard endpoint-agent prototype")
    parser.add_argument("--server", default="http://127.0.0.1:8090", help="Extreme IP Guard server URL")
    subparsers = parser.add_subparsers(dest="command", required=True)

    heartbeat = subparsers.add_parser("heartbeat", help="Submit transparent asset posture telemetry")
    heartbeat.add_argument("--asset-id", default="local-endpoint", help="Stable endpoint asset id")
    heartbeat.add_argument("--hostname", default="", help="Endpoint hostname")
    heartbeat.add_argument("--owner", default="", help="Responsible owner")
    heartbeat.add_argument("--department", default="General", help="Department or business unit")
    heartbeat.add_argument("--ip-address", default="", help="Endpoint IP address to classify")
    heartbeat.add_argument("--os-name", default="", help="Operating-system display name")
    heartbeat.add_argument("--patch-age-days", type=int, default=0)
    heartbeat.add_argument("--critical-vulns", type=int, default=0)
    heartbeat.add_argument("--high-vulns", type=int, default=0)
    heartbeat.add_argument("--failed-logins", type=int, default=0)
    heartbeat.add_argument("--dlp-incidents", type=int, default=0)
    heartbeat.add_argument("--unusual-egress-mb", type=int, default=0)
    heartbeat.add_argument("--encryption-disabled", action="store_true")
    heartbeat.add_argument("--edr-disabled", action="store_true")
    heartbeat.add_argument("--firewall-disabled", action="store_true")
    heartbeat.add_argument("--external-exposure", action="store_true")
    heartbeat.add_argument("--sensitive-data", action="store_true")
    heartbeat.set_defaults(func=send_heartbeat)

    dlp = subparsers.add_parser("dlp-event", help="Submit a simulated DLP decision event")
    dlp.add_argument("--asset-ref", default="", help="Asset id, hostname, or numeric id")
    dlp.add_argument("--username", default="", help="User associated with the data movement")
    dlp.add_argument("--channel", required=True, help="Data channel, e.g. email, external_upload, removable_media")
    dlp.add_argument("--sensitivity", required=True, choices=["public", "internal", "confidential", "secret"])
    dlp.add_argument("--destination", default="", help="Destination label or domain")
    dlp.add_argument("--destination-trusted", action="store_true")
    dlp.add_argument("--bytes-count", type=int, default=0)
    dlp.add_argument("--encrypted", action="store_true")
    dlp.add_argument("--user-override", action="store_true")
    dlp.set_defaults(func=send_dlp_event)

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


"""Extreme Printer Controller prototype.

This CLI represents the printer-side or gateway-side controller. Real embedded
packages must be implemented per vendor SDK; this prototype defines the shared
control flow and adapter metadata.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from epms.agents import build_heartbeat, platform_profile, supported_platforms


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


def list_platforms(_: argparse.Namespace) -> object:
    return supported_platforms()


def send_heartbeat(args: argparse.Namespace) -> object:
    profile = platform_profile(args.vendor)
    metadata = {
        "mode": "printer-controller",
        "vendor": profile["vendor"],
        "platform": profile["platform"],
        "embedded": profile["embedded"],
        "capabilities": profile["capabilities"],
        "model": args.model,
        "device_address": args.device_address,
    }
    heartbeat = build_heartbeat(
        agent_id=args.agent_id or f"printer-controller-{profile['vendor']}-{socket.gethostname()}",
        agent_type="printer-controller",
        metadata=metadata,
    )
    return request_json(args.server, "/api/agents/heartbeat", heartbeat.to_dict())


def release_job(args: argparse.Namespace) -> object:
    return request_json(args.server, f"/api/jobs/{args.job_id}/release", {})


def deny_job(args: argparse.Namespace) -> object:
    return request_json(args.server, f"/api/jobs/{args.job_id}/deny", {"reason": args.reason})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme Printer Controller prototype")
    parser.add_argument("--server", default="http://127.0.0.1:8080", help="Extreme Server URL")
    subparsers = parser.add_subparsers(dest="command", required=True)

    platforms = subparsers.add_parser("platforms", help="List supported embedded/gateway platforms")
    platforms.set_defaults(func=list_platforms)

    heartbeat = subparsers.add_parser("heartbeat", help="Register or refresh a printer controller")
    heartbeat.add_argument("--vendor", default="generic", help="Printer vendor, e.g. hp, canon, ricoh")
    heartbeat.add_argument("--model", default="Unknown MFD")
    heartbeat.add_argument("--device-address", default="")
    heartbeat.add_argument("--agent-id", default="")
    heartbeat.set_defaults(func=send_heartbeat)

    release = subparsers.add_parser("release", help="Release a held job from the printer UI")
    release.add_argument("--job-id", type=int, required=True)
    release.set_defaults(func=release_job)

    deny = subparsers.add_parser("deny", help="Deny a held job from the printer UI")
    deny.add_argument("--job-id", type=int, required=True)
    deny.add_argument("--reason", default="Denied from printer controller")
    deny.set_defaults(func=deny_job)

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

"""Extreme Printer Controller — embedded and gateway device control."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from epms.agents import build_heartbeat, platform_profile, supported_platforms
from epms.embedded import get_adapter
from epms.ipp_client import build_get_jobs_request, ipp_get_jobs, parse_get_jobs_response
from epms.security import AGENT_TOKEN_HEADER


def request_json(server_url: str, path: str, payload: dict | None = None, agent_token: str = "") -> object:
    url = server_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if agent_token:
        headers[AGENT_TOKEN_HEADER] = agent_token
    request = Request(url, data=data, headers=headers)
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
    adapter = get_adapter(
        vendor=args.vendor,
        server_url=args.server,
        agent_token=args.agent_token,
        device_address=args.device_address,
    )
    metadata = {
        "mode": "printer-controller",
        "vendor": profile["vendor"],
        "platform": profile["platform"],
        "embedded": profile["embedded"],
        "capabilities": profile["capabilities"],
        "model": args.model,
        "device_address": args.device_address,
        "adapter": adapter.device_capabilities(),
    }
    heartbeat = build_heartbeat(
        agent_id=args.agent_id or f"printer-controller-{profile['vendor']}",
        agent_type="printer-controller",
        metadata=metadata,
    )
    return request_json(args.server, "/api/agents/heartbeat", heartbeat.to_dict(), args.agent_token)


def device_login(args: argparse.Namespace) -> object:
    adapter = get_adapter(
        vendor=args.vendor,
        server_url=args.server,
        agent_token=args.agent_token,
        device_address=args.device_address,
    )
    session = adapter.authenticate(username=args.username, pin=args.pin, card_id=args.card_id)
    return {"session": asdict(session), "capabilities": adapter.device_capabilities()}


def list_held(args: argparse.Namespace) -> object:
    adapter = get_adapter(
        vendor=args.vendor,
        server_url=args.server,
        agent_token=args.agent_token,
        device_address=args.device_address,
    )
    jobs = adapter.list_held_jobs(username=args.username)
    return {"jobs": [asdict(job) for job in jobs]}


def release_job(args: argparse.Namespace) -> object:
    adapter = get_adapter(
        vendor=args.vendor,
        server_url=args.server,
        agent_token=args.agent_token,
        device_address=args.device_address,
    )
    return adapter.release_job(args.job_id, username=args.username)


def deny_job(args: argparse.Namespace) -> object:
    adapter = get_adapter(
        vendor=args.vendor,
        server_url=args.server,
        agent_token=args.agent_token,
        device_address=args.device_address,
    )
    return adapter.deny_job(args.job_id, username=args.username, reason=args.reason)


def ipp_discover(args: argparse.Namespace) -> object:
    if args.response_file:
        payload = args.response_file.read_bytes()
        jobs = parse_get_jobs_response(payload)
    else:
        jobs = ipp_get_jobs(args.printer_uri)
    return {"printer_uri": args.printer_uri, "jobs": [asdict(job) for job in jobs]}


def ipp_build_request(args: argparse.Namespace) -> object:
    payload = build_get_jobs_request(printer_uri=args.printer_uri)
    return {"printer_uri": args.printer_uri, "bytes": len(payload), "preview_hex": payload[:32].hex()}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extreme Printer Controller")
    parser.add_argument("--server", default="http://127.0.0.1:8080")
    parser.add_argument("--agent-token", default=os.environ.get("EPMS_AGENT_TOKEN", ""))
    parser.add_argument("--vendor", default="generic")
    parser.add_argument("--device-address", default="")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("platforms").set_defaults(func=list_platforms)

    hb = sub.add_parser("heartbeat")
    hb.add_argument("--model", default="Unknown MFD")
    hb.add_argument("--agent-id", default="")
    hb.set_defaults(func=send_heartbeat)

    login = sub.add_parser("login", help="Authenticate user at device or gateway")
    login.add_argument("--username", required=True)
    login.add_argument("--pin", default="")
    login.add_argument("--card-id", default="")
    login.set_defaults(func=device_login)

    held = sub.add_parser("list-held", help="List held jobs for user")
    held.add_argument("--username", required=True)
    held.set_defaults(func=list_held)

    rel = sub.add_parser("release", help="Release held job")
    rel.add_argument("--job-id", type=int, required=True)
    rel.add_argument("--username", required=True)
    rel.set_defaults(func=release_job)

    deny = sub.add_parser("deny", help="Deny held job")
    deny.add_argument("--job-id", type=int, required=True)
    deny.add_argument("--username", required=True)
    deny.add_argument("--reason", default="Denied from printer controller")
    deny.set_defaults(func=deny_job)

    ipp = sub.add_parser("ipp-jobs", help="Query IPP printer jobs")
    ipp.add_argument("--printer-uri", required=True)
    ipp.add_argument("--response-file", type=argparse.FileType("rb"))
    ipp.set_defaults(func=ipp_discover)

    ipp_req = sub.add_parser("ipp-build-request", help="Show IPP Get-Jobs request size")
    ipp_req.add_argument("--printer-uri", required=True)
    ipp_req.set_defaults(func=ipp_build_request)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        print(json.dumps(args.func(args), indent=2, ensure_ascii=False))
        return 0
    except (RuntimeError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

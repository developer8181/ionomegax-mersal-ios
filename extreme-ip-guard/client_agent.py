#!/usr/bin/env python3
"""Extreme Endpoint Agent prototype — workstation telemetry and policy checks."""

from __future__ import annotations

import argparse
import json
import platform
import urllib.error
import urllib.request

from eig.agents import AGENT_VERSION, build_heartbeat_payload, default_agent_id


def post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Extreme IP Guard Endpoint Agent (prototype)")
    parser.add_argument("--server", default="http://127.0.0.1:8090", help="Extreme Server URL")
    parser.add_argument("--agent-id", default="", help="Stable agent identifier")
    parser.add_argument(
        "--action",
        choices=["heartbeat", "simulate-dlp", "simulate-usb", "zt-check"],
        default="heartbeat",
    )
    args = parser.parse_args()

    agent_id = args.agent_id or default_agent_id()
    base = args.server.rstrip("/")

    if args.action == "heartbeat":
        payload = build_heartbeat_payload(
            agent_id=agent_id,
            agent_type="endpoint",
            version=AGENT_VERSION,
            trust_score=75,
            posture={
                "encrypted_disk": True,
                "av_updated": True,
                "patch_level_ok": True,
                "agent_healthy": True,
            },
        )
        payload["user_name"] = platform.node()
        result = post_json(f"{base}/api/agents/heartbeat", payload)
        print(json.dumps(result, indent=2))
        return

    if args.action == "zt-check":
        result = post_json(
            f"{base}/api/zero-trust/check",
            {
                "posture": {
                    "encrypted_disk": True,
                    "av_updated": True,
                    "patch_level_ok": True,
                    "agent_healthy": True,
                },
                "user_mfa": True,
                "segment": "corporate",
            },
        )
        print(json.dumps(result, indent=2))
        return

    simulations = {
        "simulate-dlp": {
            "agent_id": agent_id,
            "hostname": platform.node(),
            "category": "dlp",
            "summary": "Outbound email with confidential project attachment",
            "detail": "Subject contains TOP SECRET keyword in body",
        },
        "simulate-usb": {
            "agent_id": agent_id,
            "hostname": platform.node(),
            "category": "usb",
            "summary": "USB mass storage device inserted",
            "detail": "Removable drive copy to external media",
        },
    }
    try:
        result = post_json(f"{base}/api/events", simulations[args.action])
        print(json.dumps(result, indent=2))
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()

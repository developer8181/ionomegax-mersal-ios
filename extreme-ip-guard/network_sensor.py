#!/usr/bin/env python3
"""Extreme Network Sensor prototype — edge detection and lateral-movement signals."""

from __future__ import annotations

import argparse
import json
import platform
import urllib.request

from eig.agents import AGENT_VERSION, default_agent_id


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
    parser = argparse.ArgumentParser(description="Extreme IP Guard Network Sensor (prototype)")
    parser.add_argument("--server", default="http://127.0.0.1:8090", help="Extreme Server URL")
    parser.add_argument(
        "--scenario",
        choices=["rogue-connect", "port-scan", "heartbeat"],
        default="rogue-connect",
    )
    args = parser.parse_args()
    base = args.server.rstrip("/")
    agent_id = default_agent_id(hostname=f"net-{platform.node()}")

    if args.scenario == "heartbeat":
        payload = {
            "agent_id": agent_id,
            "agent_type": "network_sensor",
            "hostname": f"sensor-{platform.node()}",
            "version": AGENT_VERSION,
            "trust_score": 90,
            "posture": {"agent_healthy": True},
        }
        print(json.dumps(post_json(f"{base}/api/agents/heartbeat", payload), indent=2))
        return

    scenarios = {
        "rogue-connect": {
            "agent_id": agent_id,
            "hostname": "ws-guest-02",
            "category": "network",
            "summary": "Unauthorized connect attempt from guest segment",
            "detail": "External host tried unauthorized access to internal file server",
        },
        "port-scan": {
            "agent_id": agent_id,
            "hostname": "ws-dev-14",
            "category": "network",
            "summary": "Port scan detected on engineering VLAN",
            "detail": "SYN flood pattern against multiple hosts",
        },
    }
    print(json.dumps(post_json(f"{base}/api/events", scenarios[args.scenario]), indent=2))


if __name__ == "__main__":
    main()

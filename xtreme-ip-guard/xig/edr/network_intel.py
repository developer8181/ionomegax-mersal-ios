# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""EDR network connection monitoring."""

from __future__ import annotations

import re
import subprocess
from typing import Any

SUSPICIOUS_REMOTE_PORTS = {4444, 5555, 6666, 31337, 1337}
KNOWN_BAD_NETS = ("185.220.", "45.142.", "91.219.")


def collect_network_connections(*, limit: int = 40) -> list[dict[str, Any]]:
    flows: list[dict[str, Any]] = []
    try:
        output = subprocess.run(
            ["ss", "-Htn"],
            capture_output=True,
            text=True,
            timeout=6,
        )
        for line in output.stdout.splitlines()[:limit]:
            parts = line.split()
            if len(parts) < 5:
                continue
            state = parts[0]
            local = parts[3] if len(parts) > 3 else ""
            remote = parts[4] if len(parts) > 4 else ""
            flows.append(
                {
                    "protocol": "tcp",
                    "local_addr": local,
                    "remote_addr": remote,
                    "state": state,
                    "risk": _score_flow(remote, state),
                }
            )
    except (OSError, subprocess.SubprocessError):
        return flows
    return flows


def suspicious_flows(flows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [f for f in flows if int(f.get("risk", 0)) >= 50]


def _score_flow(remote: str, state: str) -> int:
    risk = 0
    port_match = re.search(r":(\d+)$", remote)
    if port_match:
        port = int(port_match.group(1))
        if port in SUSPICIOUS_REMOTE_PORTS:
            risk += 60
        if port > 49152 and state == "ESTAB":
            risk += 15
    for net in KNOWN_BAD_NETS:
        if net in remote:
            risk += 70
    return min(100, risk)

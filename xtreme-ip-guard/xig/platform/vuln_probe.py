"""Host vulnerability probe signals sent with agent heartbeats."""

from __future__ import annotations

import platform
import re
import socket
import subprocess
from typing import Any


def collect_vuln_probe(security_features: dict[str, Any] | None = None) -> dict[str, Any]:
    security_features = security_features or {}
    ports = _listening_ports()
    return {
        "open_ports": sorted(ports),
        "listening_ports": [{"local": f"0.0.0.0:{port}", "state": "LISTEN"} for port in ports[:15]],
        "security_features": security_features,
        "os_probe": platform.platform(),
        "probe_version": "2.0",
    }


def _listening_ports() -> list[int]:
    ports: list[int] = []
    try:
        output = subprocess.run(
            ["ss", "-lnt"],
            check=False,
            capture_output=True,
            text=True,
            timeout=4,
        )
        for line in output.stdout.splitlines()[1:25]:
            match = re.search(r":(\d+)\s", line)
            if match:
                ports.append(int(match.group(1)))
    except (OSError, subprocess.SubprocessError):
        for port in (22, 80, 443, 445, 3389, 8080):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(0.15)
                    if sock.connect_ex(("127.0.0.1", port)) == 0:
                        ports.append(port)
            except OSError:
                continue
    return sorted(set(ports))

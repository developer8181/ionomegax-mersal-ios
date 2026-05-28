# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Optional nmap service discovery when installed on the management host."""

from __future__ import annotations

import re
import shutil
import subprocess
from typing import Any


def nmap_available() -> bool:
    return shutil.which("nmap") is not None


def scan_host_ports(target: str, *, max_ports: int = 200) -> dict[str, Any]:
    """Run a fast TCP scan against endpoint hostname/IP (management network)."""
    if not nmap_available():
        return {"available": False, "ports": [], "services": []}
    if not target or target in {"localhost", "127.0.0.1"}:
        target = "127.0.0.1"
    cmd = [
        "nmap",
        "-Pn",
        "-sT",
        "-T4",
        "--open",
        "-F",
        target,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return {"available": True, "ports": [], "services": [], "error": "scan_failed"}

    ports: list[int] = []
    services: list[dict[str, str]] = []
    for line in proc.stdout.splitlines():
        match = re.match(r"(\d+)/tcp\s+open\s+(\S+)", line)
        if match:
            port = int(match.group(1))
            ports.append(port)
            services.append({"port": str(port), "service": match.group(2)})
            if len(ports) >= max_ports:
                break
    return {"available": True, "ports": sorted(set(ports)), "services": services}

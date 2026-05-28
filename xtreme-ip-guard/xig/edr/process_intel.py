# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""EDR-lite process intelligence on endpoints."""

from __future__ import annotations

import re
import subprocess
from typing import Any

SUSPICIOUS_PATTERNS = (
    r"mimikatz",
    r"powershell.*-enc",
    r"cmd\.exe.*/c.*curl",
    r"nc\.exe",
    r"ncat",
    r"crypt",
    r"locker",
    r"ransom",
    r"keylog",
)


def collect_running_processes(*, limit: int = 40) -> list[dict[str, Any]]:
    processes: list[dict[str, Any]] = []
    try:
        output = subprocess.run(
            ["ps", "-eo", "pid,user,comm,args"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        for line in output.stdout.splitlines()[1 : limit + 1]:
            parts = line.strip().split(None, 3)
            if len(parts) < 4:
                continue
            processes.append(
                {
                    "pid": parts[0],
                    "user": parts[1],
                    "comm": parts[2],
                    "args": parts[3][:200],
                }
            )
    except (OSError, subprocess.SubprocessError):
        return processes
    return processes


def suspicious_process_events(processes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from ..platform.base import SensorEvent

    events: list[SensorEvent] = []
    for proc in processes:
        blob = f"{proc.get('comm', '')} {proc.get('args', '')}".lower()
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, blob):
                events.append(
                    SensorEvent(
                        event_type="process_alert",
                        channel="endpoint_process",
                        resource=str(proc.get("comm", "unknown")),
                        classification="malware",
                        destination=str(proc.get("args", ""))[:120],
                        severity=35,
                        behavior_flags=("new_process", "unsigned_process"),
                        metadata={"pid": proc.get("pid"), "user": proc.get("user"), "pattern": pattern},
                    )
                )
                break
    return events

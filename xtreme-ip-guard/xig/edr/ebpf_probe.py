# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""eBPF / bpftool probe — advanced EDR telemetry when available on Linux."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any


def ebpf_available() -> bool:
    return shutil.which("bpftool") is not None


def collect_ebpf_snapshot() -> dict[str, Any]:
    if not ebpf_available():
        return {"available": False}
    try:
        prog = subprocess.check_output(
            ["bpftool", "prog", "list", "--json"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=8,
        )
        programs = json.loads(prog) if prog.strip().startswith("[") else []
        return {
            "available": True,
            "program_count": len(programs) if isinstance(programs, list) else 0,
            "sample": programs[:5] if isinstance(programs, list) else [],
        }
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {"available": True, "program_count": 0, "error": "bpftool parse failed"}

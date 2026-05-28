# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Agent-side eBPF EDR — kernel telemetry and threat heuristics via bpftool."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

SUSPICIOUS_BPF_PATTERNS = (
    r"keylog",
    r"rootkit",
    r"backdoor",
    r"hide_",
    r"syscall",
    r"exfil",
    r"mimikatz",
    r"dump_creds",
)

PRIVILEGED_PROG_TYPES = frozenset({"kprobe", "kretprobe", "tracepoint", "raw_tracepoint", "lsm", "cgroup_skb"})


def collect_agent_ebpf_edr(*, include_detections: bool = True) -> dict[str, Any]:
    """Full eBPF EDR payload for agent heartbeat (Linux only)."""
    if os.name != "posix" or not Path("/proc").is_dir():
        return {"available": False, "reason": "not_linux"}
    from .ebpf_probe import collect_ebpf_snapshot, ebpf_available

    snapshot = collect_ebpf_snapshot()
    if not snapshot.get("available"):
        return snapshot

    maps_info = _bpftool_json(["map", "list"])
    links_info = _bpftool_json(["link", "list"])
    programs = snapshot.get("sample") or _bpftool_json(["prog", "list"])[:20]

    result: dict[str, Any] = {
        "available": True,
        "engine": "mersal-ebpf-edr",
        "program_count": snapshot.get("program_count", len(programs)),
        "map_count": len(maps_info) if isinstance(maps_info, list) else 0,
        "link_count": len(links_info) if isinstance(links_info, list) else 0,
        "programs_sample": programs[:8],
        "kernel_btf": Path("/sys/kernel/btf/vmlinux").is_file(),
    }

    if include_detections:
        result["edr_detections"] = build_ebpf_edr_detections(programs, result)
    return result


def build_ebpf_edr_detections(programs: list[Any], context: dict[str, Any]) -> list[dict[str, Any]]:
    detections: list[dict[str, Any]] = []
    if not isinstance(programs, list):
        return detections

    for prog in programs:
        if not isinstance(prog, dict):
            continue
        name = str(prog.get("name", "") or prog.get("prog", "")).lower()
        prog_type = str(prog.get("type", "")).lower()
        for pattern in SUSPICIOUS_BPF_PATTERNS:
            if re.search(pattern, name):
                detections.append(
                    {
                        "type": "ebpf_suspicious_program",
                        "severity": 88,
                        "title": f"Suspicious eBPF program name: {name or 'unknown'}",
                        "pattern": pattern,
                        "program": prog,
                    }
                )
                break
        if prog_type in PRIVILEGED_PROG_TYPES and prog.get("uid", 0) not in (0, "0"):
            detections.append(
                {
                    "type": "ebpf_unprivileged_kernel_hook",
                    "severity": 82,
                    "title": f"Unprivileged {prog_type} BPF program loaded",
                    "program": prog,
                }
            )

    prog_count = int(context.get("program_count", 0))
    if prog_count > 80:
        detections.append(
            {
                "type": "ebpf_program_storm",
                "severity": 60,
                "title": f"High eBPF program count: {prog_count}",
                "program_count": prog_count,
            }
        )

    map_count = int(context.get("map_count", 0))
    if map_count > 200:
        detections.append(
            {
                "type": "ebpf_map_storm",
                "severity": 55,
                "title": f"High eBPF map count: {map_count}",
                "map_count": map_count,
            }
        )

    return detections


def ebpf_edr_sensor_events() -> list[dict[str, Any]]:
    """Lightweight events for platform sensor pipeline."""
    payload = collect_agent_ebpf_edr(include_detections=True)
    events: list[dict[str, Any]] = []
    for det in payload.get("edr_detections") or []:
        events.append(
            {
                "event_type": "ebpf_detection",
                "channel": "kernel",
                "resource": str(det.get("title", "ebpf")),
                "severity": int(det.get("severity", 50)),
                "metadata": det,
            }
        )
    return events


def _bpftool_json(args: list[str]) -> list[Any]:
    try:
        out = subprocess.check_output(
            ["bpftool", *args, "--json"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
        data = json.loads(out) if out.strip() else []
        return data if isinstance(data, list) else []
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return []

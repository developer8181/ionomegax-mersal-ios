"""Agent protocol helpers for endpoint and network sensor components."""

from __future__ import annotations

import platform
import uuid
from typing import Any


def default_agent_id(hostname: str | None = None) -> str:
    host = hostname or platform.node() or "unknown-host"
    return f"eig-{host}-{uuid.uuid4().hex[:8]}"


def build_heartbeat_payload(
    *,
    agent_id: str,
    agent_type: str,
    version: str,
    trust_score: int,
    posture: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "hostname": platform.node(),
        "os_name": platform.system(),
        "os_version": platform.release(),
        "version": version,
        "trust_score": trust_score,
        "posture": posture or {},
    }


def supported_agent_types() -> list[dict[str, str]]:
    return [
        {
            "type": "endpoint",
            "description": "Workstation agent — DLP, USB, app, web, print telemetry",
        },
        {
            "type": "network_sensor",
            "description": "Edge sensor — lateral movement, port policy, rogue device detection",
        },
        {
            "type": "site_gateway",
            "description": "Branch gateway — segment enforcement, offline policy cache",
        },
        {
            "type": "dlp_probe",
            "description": "Deep content inspection probe for mail and file shares",
        },
    ]


AGENT_VERSION = "0.1.0-prototype"

"""Shared agent metadata and control-profile helpers for Extreme IP Guard."""

from __future__ import annotations

import platform
import socket
from dataclasses import asdict, dataclass
from typing import Any


SUPPORTED_AGENT_TYPES = {
    "server",
    "sensor",
    "edge-enforcer",
    "site-relay",
    "deception-node",
}


SUPPORTED_CONTROL_PROFILES: dict[str, dict[str, Any]] = {
    "linux-ebpf": {
        "platform": "Linux eBPF sensor / enforcer",
        "mode": "kernel telemetry + adaptive block",
        "capabilities": ["dns visibility", "socket telemetry", "microsegmentation", "fast quarantine"],
    },
    "windows-wfp": {
        "platform": "Windows WFP + ETW",
        "mode": "endpoint telemetry + policy enforcement",
        "capabilities": ["process correlation", "firewall action", "identity tagging", "script monitoring"],
    },
    "mac-network-extension": {
        "platform": "macOS Network Extension",
        "mode": "user-space enforcement and analytics",
        "capabilities": ["per-app policy", "socket visibility", "proxy redirection"],
    },
    "ztna-gateway": {
        "platform": "Zero-trust edge gateway",
        "mode": "inline policy and identity verification",
        "capabilities": ["adaptive access", "service cloaking", "mutual TLS"],
    },
    "deception-mesh": {
        "platform": "Decoy and sinkhole fabric",
        "mode": "tripwire detection",
        "capabilities": ["honeypots", "sinkhole redirect", "credential lure"],
    },
    "generic-gateway": {
        "platform": "Generic network gateway",
        "mode": "observe or enforce",
        "capabilities": ["netflow ingest", "blocklists", "site failover"],
    },
}


@dataclass(frozen=True)
class AgentHeartbeat:
    agent_id: str
    agent_type: str
    hostname: str
    version: str
    os_name: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_control_profile(profile: str) -> str:
    value = profile.strip().lower().replace("_", "-").replace(" ", "-")
    if value in SUPPORTED_CONTROL_PROFILES:
        return value
    return "generic-gateway"


def control_profile(profile: str) -> dict[str, Any]:
    normalized = normalize_control_profile(profile)
    result = SUPPORTED_CONTROL_PROFILES[normalized].copy()
    result["id"] = normalized
    return result


def supported_control_profiles() -> list[dict[str, Any]]:
    return [control_profile(name) for name in sorted(SUPPORTED_CONTROL_PROFILES)]


def build_heartbeat(
    *,
    agent_id: str,
    agent_type: str,
    version: str = "0.1.0",
    metadata: dict[str, Any] | None = None,
) -> AgentHeartbeat:
    if agent_type not in SUPPORTED_AGENT_TYPES:
        raise ValueError(f"unsupported agent type: {agent_type}")

    clean_agent_id = agent_id.strip()
    if not clean_agent_id:
        raise ValueError("agent_id is required")

    payload = metadata.copy() if metadata else {}
    if "control_profile" in payload:
        payload["control_profile"] = normalize_control_profile(str(payload["control_profile"]))

    return AgentHeartbeat(
        agent_id=clean_agent_id,
        agent_type=agent_type,
        hostname=socket.gethostname(),
        version=version,
        os_name=f"{platform.system()} {platform.release()}",
        metadata=payload,
    )

"""Shared metadata for client agents and printer controllers."""

from __future__ import annotations

import platform
import socket
from dataclasses import dataclass, asdict
from typing import Any


SUPPORTED_AGENT_TYPES = {"server", "client", "print-provider", "printer-controller", "site-server"}


SUPPORTED_EMBEDDED_PLATFORMS: dict[str, dict[str, Any]] = {
    "hp": {
        "platform": "OXP / Workpath / FutureSmart",
        "embedded": True,
        "sdk_active": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "canon": {
        "platform": "MEAP",
        "embedded": True,
        "sdk_active": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "ricoh": {
        "platform": "SmartSDK / SOP",
        "embedded": True,
        "sdk_active": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "xerox": {
        "platform": "EIP",
        "embedded": True,
        "sdk_active": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "sharp": {
        "platform": "OSA",
        "embedded": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "konica-minolta": {
        "platform": "OpenAPI / i-Option",
        "embedded": True,
        "sdk_active": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "toshiba": {
        "platform": "e-BRIDGE Open Platform",
        "embedded": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "kyocera": {
        "platform": "HyPAS",
        "embedded": True,
        "sdk_active": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "olivetti": {
        "platform": "Olivetti Connect / INFOchip",
        "embedded": True,
        "sdk_active": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "lexmark": {
        "platform": "eSF",
        "embedded": True,
        "sdk_active": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking", "card_auth"],
        "fallback": "print-provider-gateway",
    },
    "epson": {
        "platform": "Open Connect",
        "embedded": True,
        "capabilities": ["release", "copy_tracking", "scan_tracking"],
        "fallback": "print-provider-gateway",
    },
    "generic": {
        "platform": "IPP / SNMP / CUPS / Windows Spooler gateway",
        "embedded": False,
        "capabilities": ["job_tracking", "quota_enforcement", "release_station"],
        "fallback": "release-station",
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


def normalize_vendor(vendor: str) -> str:
    value = vendor.strip().lower().replace("_", "-").replace(" ", "-")
    if value in {"konica", "konica-minolta", "konicaminolta", "km"}:
        return "konica-minolta"
    if value.startswith("olivetti") or value in {"infochip", "olivetti-infochip"}:
        return "olivetti"
    if value in SUPPORTED_EMBEDDED_PLATFORMS:
        return value
    return "generic"


def platform_profile(vendor: str) -> dict[str, Any]:
    normalized = normalize_vendor(vendor)
    profile = SUPPORTED_EMBEDDED_PLATFORMS[normalized].copy()
    profile["vendor"] = normalized
    try:
        from epms.embedded.sdk_registry import get_sdk_runtime

        profile["sdk"] = get_sdk_runtime(normalized).to_dict()
    except ImportError:
        profile["sdk"] = {"status": "unknown"}
    return profile


def supported_platforms() -> list[dict[str, Any]]:
    return [platform_profile(vendor) for vendor in sorted(SUPPORTED_EMBEDDED_PLATFORMS)]


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

    return AgentHeartbeat(
        agent_id=clean_agent_id,
        agent_type=agent_type,
        hostname=socket.gethostname(),
        version=version,
        os_name=f"{platform.system()} {platform.release()}",
        metadata=metadata or {},
    )

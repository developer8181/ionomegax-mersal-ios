"""Agent registry metadata for Extreme IP Guard distributed components."""

from __future__ import annotations

import platform
import socket
from dataclasses import asdict, dataclass
from typing import Any


SUPPORTED_AGENT_TYPES = {
    "server",
    "edge-enforcer",
    "endpoint-agent",
    "flow-collector",
    "site-server",
    "nac-gateway",
}

ENFORCEMENT_BACKENDS = {
    "nftables": {
        "platform": "Linux nftables",
        "layer": "L3/L4",
        "throughput": "high",
        "capabilities": ["cidr_block", "rate_limit", "conn_track", "geoip"],
    },
    "ebpf-xdp": {
        "platform": "Linux eBPF/XDP",
        "layer": "L2/L3 kernel",
        "throughput": "ultra-high",
        "capabilities": ["ddos_mitigation", "flow_sampling", "inline_drop"],
    },
    "wfp": {
        "platform": "Windows Filtering Platform",
        "layer": "L3/L4",
        "throughput": "high",
        "capabilities": ["app_filter", "cidr_block", "identity_aware"],
    },
    "iptables": {
        "platform": "Linux iptables (legacy)",
        "layer": "L3/L4",
        "throughput": "medium",
        "capabilities": ["cidr_block", "nat", "conn_track"],
    },
    "envoy": {
        "platform": "Envoy Proxy L7",
        "layer": "L7 reverse proxy",
        "throughput": "high",
        "capabilities": ["jwt_auth", "rate_limit", "mTLS", "path_routing"],
    },
    "sdp-controller": {
        "platform": "Software-Defined Perimeter",
        "layer": "L7 application",
        "throughput": "medium",
        "capabilities": ["single_packet_auth", "dark_network", "device_posture"],
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


def build_heartbeat(
    *,
    agent_id: str,
    agent_type: str,
    version: str = "0.1.0",
    metadata: dict[str, Any] | None = None,
) -> AgentHeartbeat:
    if agent_type not in SUPPORTED_AGENT_TYPES:
        raise ValueError(f"unsupported agent type: {agent_type}")
    clean_id = agent_id.strip()
    if not clean_id:
        raise ValueError("agent_id is required")
    return AgentHeartbeat(
        agent_id=clean_id,
        agent_type=agent_type,
        hostname=socket.gethostname(),
        version=version,
        os_name=f"{platform.system()} {platform.release()}",
        metadata=metadata or {},
    )


def supported_backends() -> list[dict[str, Any]]:
    return [{"id": key, **value} for key, value in sorted(ENFORCEMENT_BACKENDS.items())]

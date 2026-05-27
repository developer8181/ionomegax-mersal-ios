"""Core threat-scoring and policy logic for Extreme IP Guard."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass

LOCAL_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::1/128"),
)


@dataclass(frozen=True)
class GuardPolicy:
    name: str
    mode: str
    trusted_networks: tuple[str, ...]
    block_ports: tuple[int, ...]
    hard_block_countries: tuple[str, ...]
    challenge_threshold: int = 45
    block_threshold: int = 70
    quarantine_threshold: int = 90


@dataclass(frozen=True)
class NetworkEvent:
    source_ip: str
    destination_ip: str
    destination_port: int
    protocol: str
    country: str
    bytes_out: int
    bytes_in: int
    process_name: str
    ip_reputation_score: int
    tor_exit_node: bool
    geo_anomaly: bool
    burst_connections: int
    asset_criticality: str = "medium"


@dataclass(frozen=True)
class RiskDecision:
    risk_score: int
    severity: str
    action: str
    reasons: tuple[str, ...]


def normalize_ip(value: str) -> str:
    text = value.strip()
    if not text:
        raise ValueError("ip address is required")
    return ipaddress.ip_address(text).compressed


def parse_networks(values: tuple[str, ...]) -> tuple[ipaddress._BaseNetwork, ...]:
    return tuple(ipaddress.ip_network(item, strict=False) for item in values)


def is_private_or_local(value: str) -> bool:
    ip_value = ipaddress.ip_address(normalize_ip(value))
    return any(ip_value in network for network in LOCAL_NETWORKS)


def score_event(event: NetworkEvent, policy: GuardPolicy) -> RiskDecision:
    if event.destination_port <= 0 or event.destination_port > 65535:
        raise ValueError("destination_port must be between 1 and 65535")
    if event.bytes_out < 0 or event.bytes_in < 0:
        raise ValueError("traffic counters cannot be negative")
    if event.ip_reputation_score < 0 or event.ip_reputation_score > 100:
        raise ValueError("ip_reputation_score must be between 0 and 100")
    if event.burst_connections < 0:
        raise ValueError("burst_connections cannot be negative")

    source_ip = normalize_ip(event.source_ip)
    destination_ip = normalize_ip(event.destination_ip)
    reasons: list[str] = []
    score = 0
    forced_action: str | None = None

    trusted_networks = parse_networks(policy.trusted_networks)
    source_value = ipaddress.ip_address(source_ip)
    destination_value = ipaddress.ip_address(destination_ip)
    on_trusted_network = any(destination_value in network for network in trusted_networks)

    if event.country.strip().upper() in {country.upper() for country in policy.hard_block_countries}:
        score += 35
        forced_action = "quarantine"
        reasons.append("destination country is explicitly blocked by policy")

    if event.destination_port in set(policy.block_ports):
        score += 18
        reasons.append(f"destination port {event.destination_port} is sensitive")

    if event.ip_reputation_score >= 95:
        score += 40
        reasons.append("destination IP has near-certain malicious reputation")
    elif event.ip_reputation_score >= 80:
        score += 30
        reasons.append("destination IP has high-risk reputation")
    elif event.ip_reputation_score >= 60:
        score += 18
        reasons.append("destination IP has suspicious reputation")

    if event.tor_exit_node:
        score += 22
        reasons.append("destination is associated with TOR or anonymized routing")

    if event.geo_anomaly:
        score += 14
        reasons.append("traffic shows a geographic anomaly")

    if event.burst_connections >= 500:
        score += 22
        reasons.append("connection burst matches worm or scan behavior")
    elif event.burst_connections >= 200:
        score += 12
        reasons.append("connection volume is higher than normal")

    if event.bytes_out >= 50_000_000:
        score += 16
        reasons.append("large outbound transfer detected")
    elif event.bytes_out >= 10_000_000:
        score += 8
        reasons.append("elevated outbound traffic volume detected")

    process_name = event.process_name.strip().lower()
    if process_name in {"powershell.exe", "cmd.exe", "wscript.exe", "mshta.exe", "bash", "python", "osascript"}:
        score += 15
        reasons.append("living-off-the-land or scripting process generated the traffic")

    criticality = event.asset_criticality.strip().lower()
    if criticality == "critical":
        score += 10
        reasons.append("asset is classified as critical")
    elif criticality == "high":
        score += 6
        reasons.append("asset is classified as high value")

    if on_trusted_network and not event.tor_exit_node and event.ip_reputation_score < 40:
        score -= 10
        reasons.append("destination belongs to a trusted network")

    if is_private_or_local(destination_ip) and source_value.version == destination_value.version:
        score -= 8
        reasons.append("destination is private or local network space")

    score = max(0, min(score, 100))
    severity = severity_for_score(score)

    if forced_action == "quarantine":
        action = "quarantine"
    elif score >= policy.quarantine_threshold:
        action = "quarantine"
    elif score >= policy.block_threshold:
        action = "block"
    elif score >= policy.challenge_threshold:
        action = "challenge"
    elif score >= 20:
        action = "observe"
    else:
        action = "allow"

    if policy.mode == "monitor":
        action = "observe" if action in {"challenge", "block", "quarantine"} else action
        reasons.append("policy is in monitor mode")

    if not reasons:
        reasons.append("traffic is consistent with the current trust policy")

    return RiskDecision(
        risk_score=score,
        severity=severity,
        action=action,
        reasons=tuple(reasons),
    )


def severity_for_score(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 70:
        return "high"
    if score >= 45:
        return "medium"
    if score >= 20:
        return "low"
    return "info"

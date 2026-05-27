"""Behavioral threat intelligence and anomaly scoring for Extreme IP Guard."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class ThreatEvent:
    event_type: str
    source_ip: str
    severity: int
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class ThreatAssessment:
    score: int
    level: str
    triggers: tuple[str, ...]
    recommended_action: str
    auto_block: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level,
            "triggers": list(self.triggers),
            "recommended_action": self.recommended_action,
            "auto_block": self.auto_block,
        }


SEVERITY_WEIGHTS = {
    "port_scan": 25,
    "brute_force": 35,
    "lateral_movement": 40,
    "malware_beacon": 50,
    "policy_violation": 15,
    "unknown_device": 20,
    "geo_anomaly": 18,
    "rate_limit_exceeded": 22,
    "dhcp_spoof": 45,
    "arp_poison": 40,
}


def assess_threat(
    *,
    recent_events: list[dict[str, Any]],
    baseline_score: int = 0,
    window_minutes: int = 15,
) -> ThreatAssessment:
    """Score threat level from recent security events within a sliding window."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    score = baseline_score
    triggers: list[str] = []

    event_counts: dict[str, int] = {}
    for event in recent_events:
        event_type = str(event.get("event_type", ""))
        created = event.get("created_at", "")
        if created:
            try:
                ts = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
            except ValueError:
                pass
        weight = SEVERITY_WEIGHTS.get(event_type, 10)
        severity = int(event.get("severity", weight))
        score += severity
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
        triggers.append(event_type)

    if event_counts.get("port_scan", 0) >= 3:
        score += 20
        triggers.append("port_scan_escalation")
    if event_counts.get("brute_force", 0) >= 5:
        score += 25
        triggers.append("brute_force_escalation")

    score = min(score, 100)
    level = _score_to_level(score)
    auto_block = score >= 75
    action = "block" if auto_block else "monitor" if score >= 40 else "allow"

    return ThreatAssessment(
        score=score,
        level=level,
        triggers=tuple(dict.fromkeys(triggers)),
        recommended_action=action,
        auto_block=auto_block,
    )


def detect_port_scan(
    *,
    source_ip: str,
    unique_ports: int,
    unique_hosts: int,
    threshold_ports: int = 10,
    threshold_hosts: int = 5,
) -> ThreatEvent | None:
    if unique_ports >= threshold_ports or unique_hosts >= threshold_hosts:
        return ThreatEvent(
            event_type="port_scan",
            source_ip=source_ip,
            severity=SEVERITY_WEIGHTS["port_scan"],
            details={"unique_ports": unique_ports, "unique_hosts": unique_hosts},
        )
    return None


def detect_brute_force(
    *,
    source_ip: str,
    failed_attempts: int,
    target_service: str,
    threshold: int = 5,
) -> ThreatEvent | None:
    if failed_attempts >= threshold:
        return ThreatEvent(
            event_type="brute_force",
            source_ip=source_ip,
            severity=SEVERITY_WEIGHTS["brute_force"],
            details={"failed_attempts": failed_attempts, "target_service": target_service},
        )
    return None


def compute_device_trust(
    *,
    registered: bool,
    posture_compliant: bool,
    last_seen_hours: float,
    violation_count: int,
    attestation_verified: bool = False,
) -> int:
    """Compute device trust score (0-100) for zero-trust continuous verification."""
    score = 0
    if registered:
        score += 30
    if posture_compliant:
        score += 25
    if attestation_verified:
        score += 20
    if last_seen_hours <= 1:
        score += 15
    elif last_seen_hours <= 24:
        score += 10
    elif last_seen_hours <= 72:
        score += 5
    score -= min(violation_count * 5, 40)
    return max(0, min(score, 100))


def _score_to_level(score: int) -> str:
    if score >= 90:
        return "critical"
    if score >= 75:
        return "high"
    if score >= 50:
        return "medium"
    if score >= 25:
        return "low"
    return "info"

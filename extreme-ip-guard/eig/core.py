"""Policy engine, risk scoring, and enforcement decisions for Extreme IP Guard."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class EnforcementAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    QUARANTINE = "quarantine"
    ISOLATE = "isolate"


class EventCategory(str, Enum):
    DLP = "dlp"
    NETWORK = "network"
    ENDPOINT = "endpoint"
    IDENTITY = "identity"
    APPLICATION = "application"
    WEB = "web"
    USB = "usb"
    PRINT = "print"
    IM = "instant_messaging"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    category: EventCategory
    pattern: str
    action: EnforcementAction
    severity: Severity
    mitre_technique: str = ""
    description: str = ""


@dataclass(frozen=True)
class PolicyDecision:
    action: EnforcementAction
    severity: Severity
    risk_delta: int
    matched_rule_id: str
    reason: str
    mitre_technique: str = ""


@dataclass(frozen=True)
class RiskProfile:
    score: int
    level: str
    factors: tuple[str, ...]


DEFAULT_RULES: tuple[PolicyRule, ...] = (
    PolicyRule(
        "dlp-credit-card",
        EventCategory.DLP,
        r"\b(?:\d[ -]*?){13,16}\b",
        EnforcementAction.BLOCK,
        Severity.CRITICAL,
        "T1567",
        "Possible payment card data in outbound content",
    ),
    PolicyRule(
        "dlp-secret-keyword",
        EventCategory.DLP,
        r"(?i)\b(?:confidential|top\s*secret|internal\s*only)\b",
        EnforcementAction.WARN,
        Severity.HIGH,
        "T1048",
        "Sensitive classification keyword detected",
    ),
    PolicyRule(
        "net-unauthorized-lateral",
        EventCategory.NETWORK,
        r"(?i)unauthorized.*(connect|access|lateral)",
        EnforcementAction.BLOCK,
        Severity.HIGH,
        "T1021",
        "Unauthorized lateral movement attempt",
    ),
    PolicyRule(
        "net-port-scan",
        EventCategory.NETWORK,
        r"(?i)(port\s*scan|syn\s*flood|brute)",
        EnforcementAction.QUARANTINE,
        Severity.CRITICAL,
        "T1046",
        "Network reconnaissance or brute-force pattern",
    ),
    PolicyRule(
        "usb-mass-storage",
        EventCategory.USB,
        r"(?i)(usb|removable).*(insert|mount|copy)",
        EnforcementAction.WARN,
        Severity.MEDIUM,
        "T1091",
        "Removable media activity",
    ),
    PolicyRule(
        "usb-blocked-device",
        EventCategory.USB,
        r"(?i)blocked.*device",
        EnforcementAction.BLOCK,
        Severity.HIGH,
        "T1091",
        "Blocked peripheral class",
    ),
    PolicyRule(
        "web-torrent",
        EventCategory.WEB,
        r"(?i)\b(torrent|bittorrent|p2p)\b",
        EnforcementAction.BLOCK,
        Severity.MEDIUM,
        "T1105",
        "Prohibited P2P or torrent activity",
    ),
    PolicyRule(
        "app-ransomware",
        EventCategory.APPLICATION,
        r"(?i)(encrypt|ransom|\.locked)",
        EnforcementAction.ISOLATE,
        Severity.CRITICAL,
        "T1486",
        "Possible ransomware behavior",
    ),
    PolicyRule(
        "id-failed-auth",
        EventCategory.IDENTITY,
        r"(?i)(failed\s*login|bad\s*password|mfa\s*fail)",
        EnforcementAction.WARN,
        Severity.MEDIUM,
        "T1110",
        "Authentication failure cluster",
    ),
    PolicyRule(
        "print-sensitive",
        EventCategory.PRINT,
        r"(?i)(print|spool).*(confidential|secret)",
        EnforcementAction.WARN,
        Severity.MEDIUM,
        "T1052",
        "Sensitive document print attempt",
    ),
)

SEVERITY_WEIGHT: dict[Severity, int] = {
    Severity.INFO: 0,
    Severity.LOW: 5,
    Severity.MEDIUM: 15,
    Severity.HIGH: 30,
    Severity.CRITICAL: 50,
}

ACTION_WEIGHT: dict[EnforcementAction, int] = {
    EnforcementAction.ALLOW: 0,
    EnforcementAction.WARN: 10,
    EnforcementAction.BLOCK: 25,
    EnforcementAction.QUARANTINE: 40,
    EnforcementAction.ISOLATE: 60,
}


def clamp_score(value: int, *, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))


def risk_level(score: int) -> str:
    if score >= 85:
        return "critical"
    if score >= 65:
        return "high"
    if score >= 40:
        return "elevated"
    if score >= 20:
        return "guarded"
    return "normal"


def evaluate_event(
    *,
    category: str,
    summary: str,
    detail: str = "",
    endpoint_trust: int = 70,
    rules: tuple[PolicyRule, ...] | None = None,
) -> PolicyDecision:
    """Match event text against policy rules and derive enforcement."""
    import re

    active_rules = rules or DEFAULT_RULES
    haystack = f"{summary}\n{detail}".strip()
    try:
        event_category = EventCategory(category)
    except ValueError:
        event_category = None

    best: PolicyDecision | None = None
    for rule in active_rules:
        if event_category and rule.category != event_category:
            continue
        if not re.search(rule.pattern, haystack):
            continue
        candidate = PolicyDecision(
            action=rule.action,
            severity=rule.severity,
            risk_delta=SEVERITY_WEIGHT[rule.severity] + ACTION_WEIGHT[rule.action],
            matched_rule_id=rule.rule_id,
            reason=rule.description or rule.rule_id,
            mitre_technique=rule.mitre_technique,
        )
        if best is None or candidate.risk_delta > best.risk_delta:
            best = candidate

    if best is not None:
        return best

    return PolicyDecision(
        action=EnforcementAction.ALLOW,
        severity=Severity.INFO,
        risk_delta=0,
        matched_rule_id="",
        reason="No policy match",
    )


def composite_risk_score(
    *,
    base_trust: int,
    recent_event_deltas: list[int],
    anomaly_score: int = 0,
) -> RiskProfile:
    """Combine endpoint trust, recent policy hits, and UEBA anomaly into 0–100 risk."""
    event_load = sum(recent_event_deltas[-20:])
    raw = 100 - clamp_score(base_trust) + event_load + anomaly_score
    score = clamp_score(raw)
    factors: list[str] = []
    if base_trust < 60:
        factors.append("low_endpoint_trust")
    if event_load >= 30:
        factors.append("recent_policy_hits")
    if anomaly_score >= 25:
        factors.append("behavioral_anomaly")
    if not factors:
        factors.append("baseline")
    return RiskProfile(score=score, level=risk_level(score), factors=tuple(factors))


def zero_trust_session_verdict(
    *,
    device_posture: dict[str, Any],
    user_mfa: bool,
    network_segment: str,
) -> dict[str, Any]:
    """Continuous verification verdict (Zero Trust session gate prototype)."""
    checks: list[dict[str, Any]] = []
    passed = True

    for key, label in (
        ("encrypted_disk", "Full-disk encryption"),
        ("av_updated", "Endpoint protection current"),
        ("patch_level_ok", "Patch compliance"),
        ("agent_healthy", "EIG agent heartbeat"),
    ):
        ok = bool(device_posture.get(key))
        checks.append({"check": key, "label": label, "passed": ok})
        passed = passed and ok

    if not user_mfa:
        checks.append({"check": "mfa", "label": "Multi-factor authentication", "passed": False})
        passed = False

    restricted_segments = {"guest", "dmz", "unknown"}
    segment_ok = network_segment.lower() not in restricted_segments
    checks.append(
        {
            "check": "segment",
            "label": f"Network segment '{network_segment}'",
            "passed": segment_ok,
        }
    )
    passed = passed and segment_ok

    return {
        "granted": passed,
        "checks": checks,
        "recommendation": "full_access" if passed else "limited_access",
    }

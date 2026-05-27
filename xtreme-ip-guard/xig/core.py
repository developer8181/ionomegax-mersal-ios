"""Core policy and risk rules for Xtreme IP Guard."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_ACTIONS = {"allow", "monitor", "warn", "block", "quarantine", "isolate_endpoint"}

ACTION_RANK = {
    "allow": 0,
    "monitor": 1,
    "warn": 2,
    "block": 3,
    "quarantine": 4,
    "isolate_endpoint": 5,
}

CLASSIFICATION_WEIGHT = {
    "public": 5,
    "internal": 15,
    "confidential": 30,
    "secret": 45,
    "source_code": 35,
    "credential": 50,
}

CHANNEL_WEIGHT = {
    "local_file": 5,
    "clipboard": 15,
    "print": 10,
    "screen_capture": 20,
    "network_upload": 25,
    "unsanctioned_cloud": 30,
    "personal_email": 35,
    "removable_media": 30,
}

BEHAVIOR_FLAG_WEIGHT = {
    "after_hours": 5,
    "new_process": 10,
    "unsigned_process": 15,
    "mass_file_access": 20,
    "privilege_escalation": 25,
    "impossible_travel": 20,
}


@dataclass(frozen=True)
class PolicyRule:
    """A single defensive rule evaluated against endpoint telemetry."""

    rule_id: str
    name: str
    action: str
    event_type: str = "*"
    classification: str = "*"
    channel: str = "*"
    destination_contains: str = ""
    min_risk: int = 0
    reason: str = ""
    enabled: bool = True

    def __post_init__(self) -> None:
        if self.action not in VALID_ACTIONS:
            raise ValueError(f"unsupported policy action: {self.action}")
        if not 0 <= self.min_risk <= 100:
            raise ValueError("min_risk must be between 0 and 100")


@dataclass(frozen=True)
class EndpointEvent:
    """Normalized endpoint, DLP, network, or user-behavior event."""

    endpoint_id: str
    actor: str
    event_type: str
    channel: str
    resource: str
    classification: str = "internal"
    destination: str = ""
    process: str = ""
    severity: int = 10
    behavior_flags: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.endpoint_id:
            raise ValueError("endpoint_id is required")
        if not self.actor:
            raise ValueError("actor is required")
        if not self.event_type:
            raise ValueError("event_type is required")
        if not 0 <= self.severity <= 100:
            raise ValueError("severity must be between 0 and 100")


@dataclass(frozen=True)
class PolicyDecision:
    """Result of evaluating a telemetry event against risk and policy rules."""

    action: str
    risk_score: int
    reason: str
    matched_rule_id: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)


def normalize_text(value: str) -> str:
    return value.strip().lower()


def calculate_risk_score(event: EndpointEvent, *, endpoint_trust: int = 70) -> int:
    """Calculate a deterministic risk score from normalized defensive telemetry."""

    if not 0 <= endpoint_trust <= 100:
        raise ValueError("endpoint_trust must be between 0 and 100")

    classification = normalize_text(event.classification)
    channel = normalize_text(event.channel)
    destination = normalize_text(event.destination)

    score = int(event.severity)
    score += CLASSIFICATION_WEIGHT.get(classification, 20)
    score += CHANNEL_WEIGHT.get(channel, 15)
    score += max(0, 70 - endpoint_trust) // 2

    if destination:
        if any(marker in destination for marker in ("gmail.", "outlook.", "yahoo.", "proton.")):
            score += 18
        if any(marker in destination for marker in ("pastebin", "anonfiles", "mega.", "dropbox.")):
            score += 15
        if destination.startswith(("http://", "ftp://")):
            score += 12
        if "unknown" in destination or destination in {"external", "internet"}:
            score += 10

    for flag in event.behavior_flags:
        score += BEHAVIOR_FLAG_WEIGHT.get(normalize_text(flag), 8)

    return max(0, min(score, 100))


def default_action_for_risk(risk_score: int) -> str:
    if risk_score >= 85:
        return "isolate_endpoint"
    if risk_score >= 70:
        return "block"
    if risk_score >= 50:
        return "warn"
    if risk_score >= 25:
        return "monitor"
    return "allow"


def evaluate_event(
    event: EndpointEvent,
    policies: list[PolicyRule],
    *,
    endpoint_trust: int = 70,
) -> PolicyDecision:
    risk_score = calculate_risk_score(event, endpoint_trust=endpoint_trust)
    default_action = default_action_for_risk(risk_score)
    best_rule: PolicyRule | None = None

    for policy in policies:
        if policy.enabled and policy_matches(policy, event, risk_score):
            if best_rule is None or ACTION_RANK[policy.action] > ACTION_RANK[best_rule.action]:
                best_rule = policy

    if best_rule is None:
        return PolicyDecision(
            action=default_action,
            risk_score=risk_score,
            reason=f"Default zero-trust risk policy selected action '{default_action}'",
            tags=decision_tags(event, risk_score),
        )

    return PolicyDecision(
        action=best_rule.action,
        risk_score=risk_score,
        reason=best_rule.reason or best_rule.name,
        matched_rule_id=best_rule.rule_id,
        tags=decision_tags(event, risk_score),
    )


def policy_matches(policy: PolicyRule, event: EndpointEvent, risk_score: int) -> bool:
    if risk_score < policy.min_risk:
        return False
    if not _wildcard_equal(policy.event_type, event.event_type):
        return False
    if not _wildcard_equal(policy.classification, event.classification):
        return False
    if not _wildcard_equal(policy.channel, event.channel):
        return False
    if policy.destination_contains:
        return normalize_text(policy.destination_contains) in normalize_text(event.destination)
    return True


def decision_tags(event: EndpointEvent, risk_score: int) -> tuple[str, ...]:
    tags = [f"classification:{normalize_text(event.classification)}", f"channel:{normalize_text(event.channel)}"]
    if risk_score >= 70:
        tags.append("high_risk")
    if event.behavior_flags:
        tags.append("behavior_anomaly")
    return tuple(tags)


def _wildcard_equal(rule_value: str, event_value: str) -> bool:
    rule_value = normalize_text(rule_value)
    if rule_value in {"", "*", "any"}:
        return True
    return rule_value == normalize_text(event_value)

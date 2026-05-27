"""Extreme IP Guard - adaptive IP risk engine.

This module provides a lightweight, dependency-free foundation that can be
used inside API gateways, WAF plugins, or authentication services.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


class Decision(str, Enum):
    ALLOW = "allow"
    THROTTLE = "throttle"
    CHALLENGE = "challenge_mfa"
    BLOCK = "block"


@dataclass(frozen=True)
class RiskSignal:
    """Input telemetry normalized from different sensors."""

    ip: str
    intel_score: float  # 0..100 from threat-intel feeds
    failed_auth_attempts: int
    requests_per_minute: int
    geo_velocity_kmph: float
    impossible_travel: bool
    tor_exit_node: bool
    known_botnet: bool
    device_trust_score: float  # 0..100 where 100 means highly trusted device
    endpoint_sensitivity: int  # 1=public, 2=normal, 3=critical


@dataclass(frozen=True)
class PolicyProfile:
    """Policy profile controls strictness and response thresholds."""

    name: str
    block_threshold: float
    challenge_threshold: float
    throttle_threshold: float
    reputation_weight: float
    behavior_weight: float
    trust_weight: float

    @staticmethod
    def balanced() -> "PolicyProfile":
        return PolicyProfile(
            name="balanced",
            block_threshold=85,
            challenge_threshold=65,
            throttle_threshold=45,
            reputation_weight=0.45,
            behavior_weight=0.40,
            trust_weight=0.15,
        )

    @staticmethod
    def strict() -> "PolicyProfile":
        return PolicyProfile(
            name="strict",
            block_threshold=78,
            challenge_threshold=58,
            throttle_threshold=35,
            reputation_weight=0.50,
            behavior_weight=0.35,
            trust_weight=0.15,
        )


@dataclass(frozen=True)
class RiskAssessment:
    ip: str
    score: float
    decision: Decision
    reasons: tuple[str, ...]


class ExtremeIPGuardEngine:
    """Adaptive risk scorer for IP-based access decisions."""

    def __init__(self, policy: PolicyProfile | None = None) -> None:
        self.policy = policy or PolicyProfile.balanced()

    def assess(self, signal: RiskSignal) -> RiskAssessment:
        reputation_score = _clamp(signal.intel_score)
        behavior_score = self._behavior_score(signal)
        trust_penalty = 100.0 - _clamp(signal.device_trust_score)

        weighted_total = (
            reputation_score * self.policy.reputation_weight
            + behavior_score * self.policy.behavior_weight
            + trust_penalty * self.policy.trust_weight
        )
        adjusted = self._apply_context(weighted_total, signal)
        score = _clamp(adjusted)

        decision = self._decision(score)
        reasons = self._reasons(signal, score, decision)
        return RiskAssessment(ip=signal.ip, score=score, decision=decision, reasons=reasons)

    def _behavior_score(self, signal: RiskSignal) -> float:
        score = 0.0
        score += min(40.0, signal.failed_auth_attempts * 4.5)
        score += min(25.0, signal.requests_per_minute / 5.0)
        if signal.geo_velocity_kmph > 900:
            score += 15.0
        if signal.impossible_travel:
            score += 20.0
        if signal.tor_exit_node:
            score += 12.0
        if signal.known_botnet:
            score += 25.0
        return _clamp(score)

    def _apply_context(self, current: float, signal: RiskSignal) -> float:
        adjusted = current
        # Critical endpoints require stricter handling with lower tolerance.
        if signal.endpoint_sensitivity == 3:
            adjusted += 12.0
        elif signal.endpoint_sensitivity == 2:
            adjusted += 5.0
        return adjusted

    def _decision(self, score: float) -> Decision:
        if score >= self.policy.block_threshold:
            return Decision.BLOCK
        if score >= self.policy.challenge_threshold:
            return Decision.CHALLENGE
        if score >= self.policy.throttle_threshold:
            return Decision.THROTTLE
        return Decision.ALLOW

    def _reasons(self, signal: RiskSignal, score: float, decision: Decision) -> tuple[str, ...]:
        reasons: list[str] = [f"final_score={score:.2f}", f"decision={decision.value}"]
        if signal.intel_score >= 70:
            reasons.append("high_threat_intelligence_score")
        if signal.failed_auth_attempts >= 5:
            reasons.append("bruteforce_pattern")
        if signal.requests_per_minute >= 120:
            reasons.append("high_request_velocity")
        if signal.impossible_travel:
            reasons.append("impossible_travel_detected")
        if signal.known_botnet:
            reasons.append("known_botnet_indicator")
        if signal.endpoint_sensitivity == 3:
            reasons.append("critical_endpoint_protection")
        return tuple(reasons)

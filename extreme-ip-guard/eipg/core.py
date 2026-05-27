"""Zero-trust policy engine for Extreme IP Guard."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class Action(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    QUARANTINE = "quarantine"
    CHALLENGE = "challenge"


class PolicyScope(str, Enum):
    GLOBAL = "global"
    ZONE = "zone"
    DEVICE = "device"
    USER = "user"


@dataclass(frozen=True)
class NetworkContext:
    source_ip: str
    destination_ip: str = "0.0.0.0"
    destination_port: int = 0
    protocol: str = "tcp"
    zone: str = "default"
    device_id: str | None = None
    user_id: str | None = None
    mac_address: str | None = None
    tags: frozenset[str] = frozenset()
    threat_score: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def normalized_protocol(self) -> str:
        return self.protocol.strip().lower()


@dataclass(frozen=True)
class PolicyRule:
    id: int
    name: str
    action: Action
    priority: int
    scope: PolicyScope
    source_cidr: str | None = None
    destination_cidr: str | None = None
    destination_ports: str | None = None
    protocols: str | None = None
    zones: str | None = None
    time_window: str | None = None
    min_trust_score: int = 0
    min_threat_score: int = 0
    max_threat_score: int = 100
    tags_required: str | None = None
    is_active: bool = True
    description: str = ""

    def matches(self, ctx: NetworkContext) -> bool:
        if not self.is_active:
            return False
        if ctx.threat_score > self.max_threat_score:
            return False
        if ctx.threat_score < self.min_threat_score:
            return False
        if not _in_time_window(self.time_window, ctx.timestamp):
            return False
        if self.zones and ctx.zone not in _split_csv(self.zones):
            return False
        if self.protocols and ctx.normalized_protocol() not in _split_csv(self.protocols):
            return False
        if self.source_cidr and not _ip_in_cidr(ctx.source_ip, self.source_cidr):
            return False
        if self.destination_cidr and not _ip_in_cidr(ctx.destination_ip, self.destination_cidr):
            return False
        if self.destination_ports and not _port_in_spec(ctx.destination_port, self.destination_ports):
            return False
        if self.tags_required:
            required = set(_split_csv(self.tags_required))
            if not required.issubset(set(ctx.tags)):
                return False
        return True


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    action: Action
    reason: str
    matched_rule_id: int | None = None
    matched_rule_name: str | None = None
    trust_score: int = 100
    threat_score: int = 0
    policy_version: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action.value,
            "reason": self.reason,
            "matched_rule_id": self.matched_rule_id,
            "matched_rule_name": self.matched_rule_name,
            "trust_score": self.trust_score,
            "threat_score": self.threat_score,
            "policy_version": self.policy_version,
            "metadata": self.metadata,
        }


DEFAULT_DENY = AccessDecision(
    allowed=False,
    action=Action.DENY,
    reason="Default deny — no matching allow policy",
    trust_score=0,
)


def evaluate_access(
    ctx: NetworkContext,
    rules: list[PolicyRule],
    *,
    policy_version: int = 0,
    default_action: Action = Action.DENY,
    device_trust_score: int = 50,
) -> AccessDecision:
    """Evaluate network context against ordered policy rules (highest priority first)."""
    if ctx.threat_score >= 90:
        return AccessDecision(
            allowed=False,
            action=Action.DENY,
            reason="Critical threat score — automatic block",
            threat_score=ctx.threat_score,
            policy_version=policy_version,
            metadata={"auto_block": True},
        )

    sorted_rules = sorted(rules, key=lambda rule: rule.priority, reverse=True)
    for rule in sorted_rules:
        if not rule.matches(ctx):
            continue
        trust = device_trust_score
        if trust < rule.min_trust_score:
            continue

        allowed = rule.action == Action.ALLOW
        if rule.action == Action.QUARANTINE:
            allowed = False
        elif rule.action == Action.CHALLENGE:
            allowed = False

        return AccessDecision(
            allowed=allowed,
            action=rule.action,
            reason=f"Matched policy: {rule.name}",
            matched_rule_id=rule.id,
            matched_rule_name=rule.name,
            trust_score=trust,
            threat_score=ctx.threat_score,
            policy_version=policy_version,
            metadata={"scope": rule.scope.value},
        )

    if default_action == Action.ALLOW:
        return AccessDecision(
            allowed=True,
            action=Action.ALLOW,
            reason="Default allow — no explicit deny",
            trust_score=device_trust_score,
            threat_score=ctx.threat_score,
            policy_version=policy_version,
        )
    return AccessDecision(
        allowed=DEFAULT_DENY.allowed,
        action=default_action,
        reason=DEFAULT_DENY.reason,
        trust_score=device_trust_score,
        threat_score=ctx.threat_score,
        policy_version=policy_version,
    )


def normalize_mac(mac: str) -> str:
    cleaned = mac.strip().lower().replace("-", ":").replace(".", "")
    if len(cleaned) == 12 and ":" not in cleaned:
        cleaned = ":".join(cleaned[i : i + 2] for i in range(0, 12, 2))
    return cleaned


def validate_ip(ip: str) -> str:
    return str(ipaddress.ip_address(ip.strip()))


def validate_cidr(cidr: str) -> str:
    return str(ipaddress.ip_network(cidr.strip(), strict=False))


def _split_csv(value: str) -> list[str]:
    return [part.strip().lower() for part in value.split(",") if part.strip()]


def _ip_in_cidr(ip: str, cidr: str) -> bool:
    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False


def _port_in_spec(port: int, spec: str) -> bool:
    if port <= 0:
        return False
    for part in _split_csv(spec.replace(" ", "")):
        if "-" in part:
            start, end = part.split("-", 1)
            if int(start) <= port <= int(end):
                return True
        elif int(part) == port:
            return True
    return False


def _in_time_window(window: str | None, moment: datetime) -> bool:
    if not window:
        return True
    # Format: HH:MM-HH:MM (UTC)
    try:
        start_raw, end_raw = window.split("-", 1)
        start_h, start_m = map(int, start_raw.strip().split(":"))
        end_h, end_m = map(int, end_raw.strip().split(":"))
        current = moment.hour * 60 + moment.minute
        start = start_h * 60 + start_m
        end = end_h * 60 + end_m
        if start <= end:
            return start <= current <= end
        return current >= start or current <= end
    except ValueError:
        return True

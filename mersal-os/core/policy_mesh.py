"""Mersal Policy Mesh — unified policy sync across holons (center, gateway, endpoint)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class HolonIdentity:
    holon_id: str
    holon_type: str  # center | gateway | endpoint
    site: str
    trust_score: int = 70
    capabilities: tuple[str, ...] = field(default_factory=tuple)


@dataclass
class PolicyBundle:
    bundle_id: str
    version: int
    rules: list[dict[str, Any]]
    issued_at: float = field(default_factory=time.time)
    signature: str = ""

    def to_json(self) -> str:
        return json.dumps(
            {
                "bundle_id": self.bundle_id,
                "version": self.version,
                "rules": self.rules,
                "issued_at": self.issued_at,
                "signature": self.signature,
            },
            sort_keys=True,
        )


def merge_bundles(local: PolicyBundle, remote: PolicyBundle) -> PolicyBundle:
    """Merge policy bundles — remote wins on version, local rules appended if newer IDs."""
    if remote.version >= local.version:
        base_rules = list(remote.rules)
        seen = {rule.get("rule_id") for rule in base_rules}
        for rule in local.rules:
            rid = rule.get("rule_id")
            if rid and rid not in seen:
                base_rules.append(rule)
        return PolicyBundle(
            bundle_id=remote.bundle_id,
            version=remote.version,
            rules=base_rules,
            issued_at=remote.issued_at,
            signature=remote.signature,
        )
    return local


def trust_adjustment(holon: HolonIdentity, event_risk: int) -> int:
    """Trust Fabric: adjust holon trust from defensive telemetry."""
    delta = max(-15, min(15, (50 - event_risk) // 5))
    return max(0, min(100, holon.trust_score + delta))

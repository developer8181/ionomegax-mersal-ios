"""SOAR playbook definitions — automated response playbooks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Playbook:
    playbook_id: str
    name: str
    trigger: str
    description: str
    enabled: bool = True


DEFAULT_PLAYBOOKS: tuple[Playbook, ...] = (
    Playbook(
        playbook_id="SOAR-CRITICAL-VULN",
        name="Isolate on critical vulnerability",
        trigger="vuln.critical",
        description="Auto-isolate endpoint when CVSS >= 9.0 finding is detected",
    ),
    Playbook(
        playbook_id="SOAR-AI-EXFIL",
        name="Quarantine AI-escalated exfiltration",
        trigger="event.ai_escalated",
        description="Quarantine endpoint after AI-confirmed high-risk exfiltration",
    ),
    Playbook(
        playbook_id="SOAR-IOC-BLOCK",
        name="Create block policy on IOC hit",
        trigger="event.ioc_hit",
        description="Suggest block policy for repeated IOC destinations",
    ),
    Playbook(
        playbook_id="SOAR-HIGH-RISK-ISOLATE",
        name="Isolate sustained high risk",
        trigger="event.risk_score",
        description="Isolate when risk score >= 90 after AI fusion",
    ),
)


def playbook_config(playbook_id: str) -> dict[str, Any]:
    configs: dict[str, dict[str, Any]] = {
        "SOAR-CRITICAL-VULN": {"min_cvss": 9.0, "action": "isolate_endpoint"},
        "SOAR-AI-EXFIL": {"min_risk": 70, "action": "quarantine"},
        "SOAR-IOC-BLOCK": {"action": "block"},
        "SOAR-HIGH-RISK-ISOLATE": {"min_risk": 90, "action": "isolate_endpoint"},
    }
    return configs.get(playbook_id, {})

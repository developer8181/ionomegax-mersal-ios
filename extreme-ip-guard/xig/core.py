"""Core domain types for Extreme IP Guard.

This module defines the value objects shared by every other component: event
kinds, severity levels, MITRE ATT&CK mapping helpers, risk scoring, and the
canonical serializer used by the audit chain.

Keeping these as small immutable dataclasses makes the rest of the system easy
to unit-test and reason about.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable


class Severity(str, Enum):
    """Severity scale aligned with common SOC tooling."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def numeric(self) -> int:
        order = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return order[self]


class EventKind(str, Enum):
    """Telemetry event kinds the agent can produce.

    The list is intentionally explicit so unknown values are rejected at the
    edge instead of being silently accepted.
    """

    PROCESS_START = "process.start"
    PROCESS_STOP = "process.stop"
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_DELETE = "file.delete"
    DEVICE_USB_ATTACH = "device.usb.attach"
    DEVICE_USB_DETACH = "device.usb.detach"
    DEVICE_BLUETOOTH = "device.bluetooth"
    DEVICE_PRINT = "device.print"
    NETWORK_CONNECT = "network.connect"
    NETWORK_DNS = "network.dns"
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    SCREEN_CAPTURE = "screen.capture"
    CLIPBOARD_COPY = "clipboard.copy"
    DLP_MATCH = "dlp.match"
    AGENT_HEARTBEAT = "agent.heartbeat"


SUPPORTED_EVENT_KINDS = frozenset(kind.value for kind in EventKind)


# MITRE ATT&CK mapping used by detection rules. Trimmed to the techniques
# referenced by the bundled rule set; new entries should be appended here so
# the catalogue stays close to the engine.
MITRE_TECHNIQUES: dict[str, dict[str, str]] = {
    "T1052.001": {
        "name": "Exfiltration over USB",
        "tactic": "Exfiltration",
    },
    "T1059": {
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution",
    },
    "T1071.001": {
        "name": "Application Layer Protocol: Web",
        "tactic": "Command and Control",
    },
    "T1078": {
        "name": "Valid Accounts",
        "tactic": "Defense Evasion / Persistence",
    },
    "T1083": {
        "name": "File and Directory Discovery",
        "tactic": "Discovery",
    },
    "T1486": {
        "name": "Data Encrypted for Impact",
        "tactic": "Impact",
    },
    "T1567": {
        "name": "Exfiltration over Web Service",
        "tactic": "Exfiltration",
    },
    "T1110": {
        "name": "Brute Force",
        "tactic": "Credential Access",
    },
    "T1543": {
        "name": "Create or Modify System Process",
        "tactic": "Persistence",
    },
    "T1027": {
        "name": "Obfuscated Files or Information",
        "tactic": "Defense Evasion",
    },
}


@dataclass(frozen=True)
class TelemetryEvent:
    """A single normalised event coming from an endpoint agent."""

    agent_id: str
    kind: str
    ts: str
    subject: str
    data: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.agent_id.strip():
            raise ValueError("agent_id is required")
        if self.kind not in SUPPORTED_EVENT_KINDS:
            raise ValueError(f"unsupported event kind: {self.kind}")
        if not self.ts:
            raise ValueError("ts is required (ISO-8601 UTC)")
        if not isinstance(self.data, dict):
            raise ValueError("data must be an object")

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "kind": self.kind,
            "ts": self.ts,
            "subject": self.subject,
            "data": self.data,
        }


@dataclass(frozen=True)
class RiskUpdate:
    """The delta the detection engine applies to a user/asset risk score."""

    subject_kind: str  # "user" | "asset" | "agent"
    subject_id: str
    delta: float
    reason: str


def utc_now_iso() -> str:
    """Return the current time as an ISO-8601 UTC string with millisecond precision."""

    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def canonical_json(payload: Any) -> str:
    """Serialize ``payload`` deterministically.

    The audit chain relies on this output being byte-stable across processes
    and Python versions, so we sort keys and disable non-ASCII escaping
    surprises that some JSON encoders introduce.
    """

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_json_default,
    )


def _json_default(value: Any) -> Any:
    if isinstance(value, Severity):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    raise TypeError(f"unsupported type for canonical_json: {type(value).__name__}")


def mitre_lookup(technique_id: str) -> dict[str, str]:
    """Return ``{name, tactic}`` for an ATT&CK technique id, or an empty dict."""

    return dict(MITRE_TECHNIQUES.get(technique_id, {}))


# ---- Risk score helpers ----------------------------------------------------

RISK_ALPHA = 0.2
RISK_CEILING = 100.0


def blend_risk(previous: float, delta: float) -> float:
    """Exponentially-weighted blend used everywhere risk is updated.

    ``previous`` is the historic score, ``delta`` is the new event's risk
    contribution. The function caps the result at :data:`RISK_CEILING` and
    never returns a negative number.
    """

    if previous < 0:
        previous = 0.0
    blended = (1.0 - RISK_ALPHA) * previous + RISK_ALPHA * delta
    if blended < 0:
        return 0.0
    return min(blended, RISK_CEILING)


def classify_risk(score: float) -> Severity:
    """Map a numeric risk score onto a coarse severity bucket."""

    if score >= 80:
        return Severity.CRITICAL
    if score >= 60:
        return Severity.HIGH
    if score >= 35:
        return Severity.MEDIUM
    if score >= 15:
        return Severity.LOW
    return Severity.INFO


def severity_at_least(value: str, threshold: Severity) -> bool:
    """True when the severity ``value`` is at least ``threshold``."""

    try:
        return Severity(value).numeric >= threshold.numeric
    except ValueError:
        return False


def normalize_iocs(items: Iterable[str]) -> list[str]:
    """Lowercase, strip, dedupe IOC values (hashes, domains, IPs)."""

    seen: list[str] = []
    out: list[str] = []
    for raw in items:
        value = (raw or "").strip().lower()
        if not value or value in seen:
            continue
        seen.append(value)
        out.append(value)
    return out

"""Policy and rule definitions for the Extreme IP Guard reference engine.

Policies are deliberately expressed as plain dictionaries so they can be
loaded from JSON/YAML, signed, distributed to agents, and unit-tested
without any extra machinery.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .core import EventKind, MITRE_TECHNIQUES, Severity, SUPPORTED_EVENT_KINDS


@dataclass(frozen=True)
class Rule:
    """A single detection rule.

    Rules use a small predicate language with the following operators on
    ``data.*`` fields:

    * ``eq``        — exact equality.
    * ``in``        — value membership.
    * ``regex``     — regular expression match.
    * ``gt`` / ``lt`` / ``ge`` / ``le`` — numeric comparison.
    * ``startswith`` / ``endswith`` / ``contains`` — substring on strings.

    Operators can be combined under ``all_of`` or ``any_of``. The combinator
    is intentionally simple so it is easy to reason about, and easy to
    serialise into the signed policy bundle.
    """

    id: str
    name: str
    kind: str
    severity: str
    risk_delta: float
    mitre: str
    when: dict[str, Any]
    response: str = "alert_only"
    description: str = ""

    def validate(self) -> None:
        if not self.id.strip():
            raise ValueError("rule.id is required")
        if self.kind not in SUPPORTED_EVENT_KINDS:
            raise ValueError(f"rule.kind not supported: {self.kind}")
        try:
            Severity(self.severity)
        except ValueError as exc:
            raise ValueError(f"rule.severity invalid: {self.severity}") from exc
        if self.mitre and self.mitre not in MITRE_TECHNIQUES:
            raise ValueError(f"rule.mitre unknown technique: {self.mitre}")
        if not isinstance(self.when, dict):
            raise ValueError("rule.when must be an object")


@dataclass(frozen=True)
class PolicyBundle:
    """A signed bundle distributed to agents."""

    version: int
    rules: list[Rule]
    iocs: dict[str, list[str]] = field(default_factory=dict)
    playbooks: list[str] = field(default_factory=list)
    issued_at: str = ""
    signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "issued_at": self.issued_at,
            "rules": [rule.__dict__ for rule in self.rules],
            "iocs": self.iocs,
            "playbooks": self.playbooks,
            "signature": self.signature,
        }


def evaluate_predicate(predicate: dict[str, Any], event_data: dict[str, Any]) -> bool:
    """Evaluate a predicate dict against an event ``data`` payload.

    Empty predicate -> always matches. Unknown operators or fields make the
    predicate evaluate to False rather than raising; this is deliberate so a
    malformed rule cannot crash the whole detection pipeline.
    """

    if not predicate:
        return True

    if "all_of" in predicate:
        return all(evaluate_predicate(child, event_data) for child in predicate["all_of"])

    if "any_of" in predicate:
        return any(evaluate_predicate(child, event_data) for child in predicate["any_of"])

    for field_name, expectation in predicate.items():
        value = event_data.get(field_name)
        if not _match_expectation(value, expectation):
            return False
    return True


def _match_expectation(value: Any, expectation: Any) -> bool:
    if not isinstance(expectation, dict):
        return value == expectation

    for op, operand in expectation.items():
        if op == "eq":
            if value != operand:
                return False
        elif op == "in":
            if value not in operand:
                return False
        elif op == "regex":
            if not isinstance(value, str) or not re.search(operand, value):
                return False
        elif op == "gt":
            if not _numeric(value) or value <= operand:
                return False
        elif op == "ge":
            if not _numeric(value) or value < operand:
                return False
        elif op == "lt":
            if not _numeric(value) or value >= operand:
                return False
        elif op == "le":
            if not _numeric(value) or value > operand:
                return False
        elif op == "startswith":
            if not isinstance(value, str) or not value.startswith(operand):
                return False
        elif op == "endswith":
            if not isinstance(value, str) or not value.endswith(operand):
                return False
        elif op == "contains":
            if not isinstance(value, (str, list, tuple)) or operand not in value:
                return False
        else:
            return False
    return True


def _numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# ---- Default rules shipped with the reference build ------------------------

DEFAULT_RULES: list[Rule] = [
    Rule(
        id="R-USB-001",
        name="Mass copy to USB device",
        kind=EventKind.FILE_WRITE.value,
        severity=Severity.HIGH.value,
        risk_delta=35.0,
        mitre="T1052.001",
        when={
            "all_of": [
                {"path": {"regex": r"^/?(media|mnt|Volumes|[A-Z]:)/"}},
                {"bytes": {"gt": 50_000_000}},
            ]
        },
        response="pb-usb-mass-copy",
        description="Large file writes to a removable mount imply staged exfiltration.",
    ),
    Rule(
        id="R-DLP-001",
        name="Document with classified marker leaving the host",
        kind=EventKind.DLP_MATCH.value,
        severity=Severity.HIGH.value,
        risk_delta=30.0,
        mitre="T1567",
        when={"label": {"in": ["confidential", "secret", "top-secret"]}},
        response="pb-malware-hash-match",
        description="DLP scanner found classified markers in egressing content.",
    ),
    Rule(
        id="R-NET-001",
        name="Outbound connection to known C2 domain",
        kind=EventKind.NETWORK_CONNECT.value,
        severity=Severity.CRITICAL.value,
        risk_delta=50.0,
        mitre="T1071.001",
        when={"ioc_match": {"eq": True}},
        response="pb-malware-hash-match",
        description="A network destination matched a threat-intel indicator.",
    ),
    Rule(
        id="R-AUTH-001",
        name="Repeated authentication failures (brute force)",
        kind=EventKind.AUTH_LOGIN.value,
        severity=Severity.MEDIUM.value,
        risk_delta=15.0,
        mitre="T1110",
        when={"failed_count": {"ge": 5}},
        response="alert_only",
        description="At least five failed logins for the same account in a short window.",
    ),
    Rule(
        id="R-PROC-001",
        name="Suspicious script interpreter chain",
        kind=EventKind.PROCESS_START.value,
        severity=Severity.MEDIUM.value,
        risk_delta=20.0,
        mitre="T1059",
        when={
            "all_of": [
                {"name": {"regex": r"(powershell|cmd|bash|sh|wscript|cscript)$"}},
                {"parent": {"regex": r"(winword|excel|outlook|acrord32|chrome|firefox)$"}},
            ]
        },
        response="alert_only",
        description="Office or browser process spawning a shell/interpreter.",
    ),
    Rule(
        id="R-FILE-001",
        name="Mass file rename consistent with ransomware",
        kind=EventKind.FILE_WRITE.value,
        severity=Severity.CRITICAL.value,
        risk_delta=60.0,
        mitre="T1486",
        when={"path": {"regex": r"\.(locked|enc|crypted|ryk|wnry)$"}},
        response="pb-malware-hash-match",
        description="File extension patterns consistent with known ransomware families.",
    ),
    Rule(
        id="R-CLIP-001",
        name="Sensitive secret copied to clipboard",
        kind=EventKind.CLIPBOARD_COPY.value,
        severity=Severity.MEDIUM.value,
        risk_delta=18.0,
        mitre="T1083",
        when={"category": {"in": ["credit_card", "private_key", "aws_secret", "api_token"]}},
        response="pb-clipboard-secret",
        description="A high-entropy or known-secret pattern hit the OS clipboard.",
    ),
]


# ---- Built-in IOC starter set (replaceable at runtime) ---------------------

DEFAULT_IOCS: dict[str, list[str]] = {
    "sha256": [
        "44d88612fea8a8f36de82e1278abb02f",  # EICAR-like marker (truncated hash placeholder)
    ],
    "domain": [
        "malware-c2.example",
        "exfil-drop.example",
    ],
    "ipv4": [
        "203.0.113.66",
    ],
}


# ---- Bundled SOAR-lite playbooks ------------------------------------------

DEFAULT_PLAYBOOKS: dict[str, dict[str, Any]] = {
    "alert_only": {
        "id": "alert_only",
        "name": "Alert only",
        "actions": [{"type": "alert"}],
        "approval_required": False,
    },
    "pb-usb-mass-copy": {
        "id": "pb-usb-mass-copy",
        "name": "USB mass-copy response",
        "actions": [
            {"type": "block_usb"},
            {"type": "screenshot"},
            {"type": "alert"},
        ],
        "approval_required": False,
    },
    "pb-malware-hash-match": {
        "id": "pb-malware-hash-match",
        "name": "Malware/IoC match response",
        "actions": [
            {"type": "kill_process"},
            {"type": "quarantine_file"},
            {"type": "isolate_host"},
            {"type": "alert"},
        ],
        "approval_required": False,
    },
    "pb-clipboard-secret": {
        "id": "pb-clipboard-secret",
        "name": "Clipboard secret response",
        "actions": [
            {"type": "wipe_clipboard"},
            {"type": "warn_user"},
            {"type": "alert"},
        ],
        "approval_required": False,
    },
}


def default_rules() -> list[Rule]:
    return list(DEFAULT_RULES)


def default_iocs() -> dict[str, list[str]]:
    return {kind: list(values) for kind, values in DEFAULT_IOCS.items()}


def default_playbooks() -> dict[str, dict[str, Any]]:
    return {pid: dict(body) for pid, body in DEFAULT_PLAYBOOKS.items()}

"""Hybrid detection engine: rules + UEBA baselines + threat-intel lookups.

The engine consumes a :class:`~xig.core.TelemetryEvent` and returns a list of
:class:`Alert` instances along with the risk-score updates to apply. It is
deliberately pure (no I/O) so it can be unit-tested without spinning up the
server, and reused as a library by any sensor or response component.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

from .core import (
    EventKind,
    RiskUpdate,
    Severity,
    TelemetryEvent,
    blend_risk,
    classify_risk,
    mitre_lookup,
    utc_now_iso,
)
from .policies import Rule, evaluate_predicate


@dataclass
class Alert:
    """A detection emitted by the engine."""

    id: str
    ts: str
    severity: str
    title: str
    rule_id: str
    mitre: str
    agent_id: str
    user_id: str
    event_kind: str
    summary: str
    response: str
    risk_delta: float
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class _Baseline:
    """Streaming mean/variance baseline using Welford-EWMA hybrid.

    Keeping the state compact (just a handful of floats) lets the reference
    server hold baselines for thousands of (agent, kind) pairs in memory.
    """

    count: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def observe(self, value: float) -> float:
        """Add a value, return its z-score (0 until we have enough data)."""

        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        self.m2 += delta * (value - self.mean)
        if self.count < 12:
            return 0.0
        variance = self.m2 / max(self.count - 1, 1)
        if variance <= 1e-9:
            return 0.0
        return (value - self.mean) / math.sqrt(variance)


class DetectionEngine:
    """Stateful detection engine.

    Holds:

    * the active rule list (loaded from a :class:`~xig.policies.PolicyBundle`),
    * IOC sets for fast O(1) lookup,
    * per-(agent, kind) numerical baselines for UEBA scoring,
    * per-user risk scores blended via :func:`xig.core.blend_risk`.

    All public methods are safe to call from a single thread; the server
    serialises calls through one connection.
    """

    def __init__(
        self,
        *,
        rules: Iterable[Rule] | None = None,
        iocs: dict[str, list[str]] | None = None,
    ) -> None:
        self._rules: list[Rule] = list(rules or [])
        self._iocs: dict[str, set[str]] = {
            kind: {value.lower() for value in values} for kind, values in (iocs or {}).items()
        }
        self._baselines: dict[tuple[str, str], _Baseline] = {}
        self._risk_user: dict[str, float] = {}
        self._risk_asset: dict[str, float] = {}

    # ---- configuration ----

    def load(self, *, rules: Iterable[Rule] | None = None, iocs: dict[str, list[str]] | None = None) -> None:
        if rules is not None:
            self._rules = list(rules)
        if iocs is not None:
            self._iocs = {kind: {v.lower() for v in values} for kind, values in iocs.items()}

    def add_ioc(self, kind: str, value: str) -> None:
        self._iocs.setdefault(kind, set()).add(value.lower())

    def known_ioc(self, kind: str, value: str) -> bool:
        return value.lower() in self._iocs.get(kind, set())

    # ---- inspection helpers ----

    @property
    def rules(self) -> list[Rule]:
        return list(self._rules)

    def risk_for_user(self, user_id: str) -> float:
        return self._risk_user.get(user_id, 0.0)

    def risk_for_asset(self, asset_id: str) -> float:
        return self._risk_asset.get(asset_id, 0.0)

    # ---- evaluation ----

    def evaluate(self, event: TelemetryEvent, *, user_id: str = "") -> tuple[list[Alert], list[RiskUpdate]]:
        """Evaluate an event and return ``(alerts, risk_updates)``.

        ``user_id`` is the resolved console user; it can be empty for
        machine-only events.
        """

        event.validate()
        alerts: list[Alert] = []
        updates: list[RiskUpdate] = []

        for ioc_alert in self._ioc_alerts(event, user_id=user_id):
            alerts.append(ioc_alert)

        for rule in self._rules:
            if rule.kind != event.kind:
                continue
            data = self._augment(event)
            if not evaluate_predicate(rule.when, data):
                continue
            alert = Alert(
                id=f"AL-{event.ts}-{rule.id}",
                ts=event.ts,
                severity=rule.severity,
                title=rule.name,
                rule_id=rule.id,
                mitre=rule.mitre,
                agent_id=event.agent_id,
                user_id=user_id,
                event_kind=event.kind,
                summary=rule.description or rule.name,
                response=rule.response,
                risk_delta=rule.risk_delta,
                data={
                    "subject": event.subject,
                    "matched_fields": list(rule.when.keys()),
                    "mitre_meta": mitre_lookup(rule.mitre),
                },
            )
            alerts.append(alert)

        anomaly_alert = self._behaviour_alert(event, user_id=user_id)
        if anomaly_alert is not None:
            alerts.append(anomaly_alert)

        for alert in alerts:
            updates.extend(self._apply_risk(alert))

        return alerts, updates

    # ---- internal helpers ----

    def _augment(self, event: TelemetryEvent) -> dict[str, Any]:
        """Extend the event data with derived signals usable by rules."""

        data = dict(event.data)
        data.setdefault("subject", event.subject)
        if event.kind == EventKind.NETWORK_CONNECT.value:
            data["ioc_match"] = (
                self.known_ioc("domain", str(data.get("domain", "")))
                or self.known_ioc("ipv4", str(data.get("ip", "")))
            )
        return data

    def _ioc_alerts(self, event: TelemetryEvent, *, user_id: str) -> list[Alert]:
        out: list[Alert] = []
        if event.kind == EventKind.FILE_WRITE.value:
            sha = str(event.data.get("sha256", "")).lower()
            if sha and self.known_ioc("sha256", sha):
                out.append(
                    Alert(
                        id=f"AL-{event.ts}-IOC-SHA256",
                        ts=event.ts,
                        severity=Severity.CRITICAL.value,
                        title="Malicious file hash detected",
                        rule_id="IOC-SHA256",
                        mitre="T1027",
                        agent_id=event.agent_id,
                        user_id=user_id,
                        event_kind=event.kind,
                        summary=f"SHA-256 {sha} matches threat intel",
                        response="pb-malware-hash-match",
                        risk_delta=50.0,
                        data={"sha256": sha},
                    )
                )
        return out

    def _behaviour_alert(self, event: TelemetryEvent, *, user_id: str) -> Alert | None:
        """Update the per-(agent, kind) baseline and emit if z-score is high."""

        observed = self._numeric_signal(event)
        if observed is None:
            return None

        key = (event.agent_id, event.kind)
        baseline = self._baselines.setdefault(key, _Baseline())
        z = baseline.observe(observed)
        if abs(z) < 3.0:
            return None

        risk_delta = min(abs(z) * 5.0, 40.0)
        severity = Severity.MEDIUM.value if abs(z) < 5.0 else Severity.HIGH.value
        return Alert(
            id=f"AL-{event.ts}-UEBA-{event.kind}",
            ts=event.ts,
            severity=severity,
            title="Behavioural anomaly",
            rule_id="UEBA-Z",
            mitre="T1078",
            agent_id=event.agent_id,
            user_id=user_id,
            event_kind=event.kind,
            summary=f"Observed value {observed:.2f} is z={z:.2f} above baseline mean {baseline.mean:.2f}",
            response="alert_only",
            risk_delta=risk_delta,
            data={"z_score": round(z, 2), "observed": observed, "baseline_mean": baseline.mean},
        )

    def _numeric_signal(self, event: TelemetryEvent) -> float | None:
        """Pick the most informative numeric field for UEBA scoring."""

        if event.kind in {EventKind.FILE_WRITE.value, EventKind.FILE_READ.value}:
            value = event.data.get("bytes")
        elif event.kind == EventKind.NETWORK_CONNECT.value:
            value = event.data.get("bytes_out") or event.data.get("bytes")
        elif event.kind == EventKind.AUTH_LOGIN.value:
            value = event.data.get("failed_count")
        else:
            return None

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    def _apply_risk(self, alert: Alert) -> list[RiskUpdate]:
        updates: list[RiskUpdate] = []
        if alert.user_id:
            blended = blend_risk(self._risk_user.get(alert.user_id, 0.0), alert.risk_delta)
            self._risk_user[alert.user_id] = blended
            updates.append(
                RiskUpdate(
                    subject_kind="user",
                    subject_id=alert.user_id,
                    delta=alert.risk_delta,
                    reason=alert.title,
                )
            )
        if alert.agent_id:
            blended_asset = blend_risk(self._risk_asset.get(alert.agent_id, 0.0), alert.risk_delta)
            self._risk_asset[alert.agent_id] = blended_asset
            updates.append(
                RiskUpdate(
                    subject_kind="asset",
                    subject_id=alert.agent_id,
                    delta=alert.risk_delta,
                    reason=alert.title,
                )
            )
        return updates


def synthesize_heartbeat(agent_id: str) -> TelemetryEvent:
    """Convenience used by the agent CLI to send a minimal heartbeat."""

    return TelemetryEvent(
        agent_id=agent_id,
        kind=EventKind.AGENT_HEARTBEAT.value,
        ts=utc_now_iso(),
        subject="heartbeat",
        data={},
    )


def severity_from_risk(score: float) -> str:
    """Public helper mirroring :func:`xig.core.classify_risk` as a string."""

    return classify_risk(score).value

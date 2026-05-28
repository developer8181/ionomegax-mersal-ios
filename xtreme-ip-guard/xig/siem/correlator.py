# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""SIEM engine — correlate endpoint events into SOC alerts."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .mitre import map_event, map_rule
from .rules import DEFAULT_SIEM_RULES

if TYPE_CHECKING:
    from ..storage import Database


class SiemCorrelator:
    def __init__(self, database: "Database") -> None:
        self.db = database
        self.db.ensure_siem_rules(DEFAULT_SIEM_RULES)

    def process_event(self, event_row: dict[str, Any]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        metadata = event_row.get("metadata") or {}
        ai_meta = metadata.get("ai") or {}
        rules = self._load_rules()

        for rule in rules:
            if not rule.get("enabled", True):
                continue
            condition = rule.get("condition") or {}
            if self._matches(event_row, condition, ai_meta):
                mitre = map_rule(str(rule["rule_id"])) or map_event(
                    str(event_row.get("event_type", "")),
                    str(event_row.get("classification", "")),
                )
                alert = self.db.create_siem_alert(
                    rule_id=str(rule["rule_id"]),
                    title=str(rule["name"]),
                    severity=int(rule.get("severity", 50)),
                    endpoint_id=str(event_row.get("endpoint_id", "")),
                    event_ids=[int(event_row["event_id"])],
                    details={
                        "rule": rule["rule_id"],
                        "event_type": event_row.get("event_type"),
                        "action": event_row.get("action"),
                        "risk_score": event_row.get("risk_score"),
                        "mitre_technique": mitre,
                    },
                )
                alerts.append(alert)
        return alerts

    def run_retrospective(self, *, limit: int = 200) -> dict[str, Any]:
        events = self.db.list_events()[:limit]
        created = 0
        for event in events:
            created += len(self.process_event(event))
        return {"events_scanned": len(events), "alerts_created": created}

    def dashboard(self) -> dict[str, Any]:
        return {
            "module": "Mersal SIEM",
            "summary": self.db.siem_summary(),
            "recent_alerts": self.db.list_siem_alerts(limit=15),
            "rules_count": len(self._load_rules()),
        }

    def _load_rules(self) -> list[dict[str, Any]]:
        with self.db.connect() as db:
            rows = db.execute("SELECT * FROM siem_rules WHERE enabled = 1").fetchall()
            rules: list[dict[str, Any]] = []
            for row in rows:
                data = dict(row)
                data["condition"] = json.loads(data.get("condition_json") or "{}")
                rules.append(data)
            return rules

    @staticmethod
    def _matches(event: dict[str, Any], condition: dict[str, Any], ai_meta: dict[str, Any]) -> bool:
        if condition.get("classification") and event.get("classification") != condition["classification"]:
            return False
        if condition.get("event_type") and event.get("event_type") != condition["event_type"]:
            return False
        if condition.get("channel") and event.get("channel") != condition["channel"]:
            return False
        if condition.get("action") and event.get("action") != condition["action"]:
            return False
        min_risk = int(condition.get("min_risk", 0))
        if min_risk and int(event.get("risk_score", 0)) < min_risk:
            return False
        if condition.get("ai_escalated") and not ai_meta.get("ai_escalated"):
            return False
        if condition.get("ioc_match") and not ai_meta.get("ioc_hits"):
            return False
        if condition.get("window_blocks"):
            return SiemCorrelator._block_storm(event, int(condition["window_blocks"]))
        return True

    @staticmethod
    def _block_storm(event: dict[str, Any], threshold: int) -> bool:
        if event.get("action") != "block":
            return False
        endpoint_id = str(event.get("endpoint_id", ""))
        recent = [
            e
            for e in event.get("_recent_same_endpoint", [])
            if e.get("action") == "block"
        ] if event.get("_recent_same_endpoint") else []
        if recent:
            return len(recent) >= threshold
        return int(event.get("risk_score", 0)) >= 60

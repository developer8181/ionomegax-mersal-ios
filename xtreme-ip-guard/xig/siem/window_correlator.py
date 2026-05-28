# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""SIEM sliding-window correlation — brute force, block storms, lateral movement."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database

DEFAULT_WINDOW_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "WIN-BRUTE-FORCE",
        "name": "Brute force pattern (failed auth burst)",
        "window_seconds": 300,
        "threshold": 8,
        "event_type": "auth_failure",
        "action_filter": "*",
        "severity": 75,
    },
    {
        "rule_id": "WIN-BLOCK-STORM",
        "name": "DLP block storm",
        "window_seconds": 600,
        "threshold": 5,
        "event_type": "*",
        "action_filter": "block",
        "severity": 65,
    },
    {
        "rule_id": "WIN-LATERAL",
        "name": "Lateral movement indicators",
        "window_seconds": 900,
        "threshold": 4,
        "event_type": "network_connection",
        "action_filter": "*",
        "severity": 80,
    },
]


class WindowCorrelator:
    def __init__(self, database: "Database") -> None:
        self.db = database
        self.db.ensure_window_rules(DEFAULT_WINDOW_RULES)

    def process_event(self, event_row: dict[str, Any]) -> list[dict[str, Any]]:
        alerts: list[dict[str, Any]] = []
        endpoint_id = str(event_row.get("endpoint_id", ""))
        for rule in self.db.list_window_rules():
            if not rule.get("enabled", True):
                continue
            if not self._event_matches_rule(event_row, rule):
                continue
            window = int(rule.get("window_seconds", 300))
            threshold = int(rule.get("threshold", 5))
            count = self.db.count_events_in_window(
                endpoint_id=endpoint_id,
                window_seconds=window,
                event_type=str(rule.get("event_type", "*")),
                action_filter=str(rule.get("action_filter", "*")),
            )
            if count >= threshold:
                alert = self.db.create_siem_alert(
                    rule_id=str(rule["rule_id"]),
                    title=f"{rule['name']} ({count}/{threshold} in {window}s)",
                    severity=int(rule.get("severity", 60)),
                    endpoint_id=endpoint_id,
                    event_ids=[int(event_row["event_id"])],
                    details={
                        "correlation": "sliding_window",
                        "count": count,
                        "threshold": threshold,
                        "window_seconds": window,
                    },
                    tenant_id=str(event_row.get("tenant_id", "default")),
                )
                alerts.append(alert)
        return alerts

    def run_retrospective(self, *, limit: int = 100) -> dict[str, Any]:
        created = 0
        for event in self.db.list_events()[:limit]:
            created += len(self.process_event(event))
        return {"events_scanned": limit, "window_alerts": created}

    @staticmethod
    def _event_matches_rule(event_row: dict[str, Any], rule: dict[str, Any]) -> bool:
        et = str(rule.get("event_type", "*"))
        af = str(rule.get("action_filter", "*"))
        if et != "*" and str(event_row.get("event_type", "")) != et:
            return False
        if af != "*" and str(event_row.get("action", "")) != af:
            return False
        return True

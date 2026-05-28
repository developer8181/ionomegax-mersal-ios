# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Incident response — cases, timeline, SOC workflow."""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class IncidentManager:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def sync_from_alerts(self, alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        incidents: list[dict[str, Any]] = []
        for alert in alerts:
            if int(alert.get("severity", 0)) < 75:
                continue
            incident = self._open_from_alert(alert)
            if incident:
                incidents.append(incident)
        return incidents

    def _open_from_alert(self, alert: dict[str, Any]) -> dict[str, Any] | None:
        endpoint_id = str(alert.get("endpoint_id", "unknown"))
        incident_id = f"INC-{endpoint_id[:12]}-{secrets.token_hex(3).upper()}"
        severity = "critical" if int(alert.get("severity", 0)) >= 90 else "high"
        incident = self.db.create_incident(
            incident_id=incident_id,
            title=str(alert.get("title", "Security incident")),
            severity=severity,
            endpoint_id=endpoint_id,
            summary=f"Auto-opened from SIEM alert #{alert.get('alert_id')}",
        )
        self.db.add_incident_timeline(
            incident_id=incident_id,
            entry_type="siem_alert",
            message=f"SIEM rule triggered: {alert.get('details', {}).get('rule', '')}",
            payload=alert,
        )
        return incident

    def close_incident(self, incident_id: str, *, actor: str = "soc-team") -> dict[str, Any]:
        self.db.add_incident_timeline(
            incident_id=incident_id,
            entry_type="status_change",
            message=f"Incident closed by {actor}",
        )
        return self.db.update_incident_status(incident_id, "closed")

    def dashboard(self) -> dict[str, Any]:
        open_incidents = self.db.list_incidents(status="open", limit=20)
        return {
            "module": "Mersal Incident Response",
            "open_count": len(open_incidents),
            "incidents": open_incidents,
        }

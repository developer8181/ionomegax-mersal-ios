# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Executive reporting — CSV exports for SOC and GRC."""

from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class ReportExporter:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def export_csv(self, report_type: str, *, tenant_id: str = "default") -> str:
        handlers = {
            "compliance": self._compliance_report,
            "incidents": self._incidents_report,
            "audit": self._audit_report,
            "siem": self._siem_report,
            "executive": self._executive_summary,
        }
        handler = handlers.get(report_type, self._executive_summary)
        return handler(tenant_id=tenant_id)

    def _executive_summary(self, *, tenant_id: str) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Mersal Global Platform — Executive Summary"])
        writer.writerow(["tenant_id", tenant_id])
        dash = self.db.dashboard()
        for key, value in dash.get("totals", {}).items():
            writer.writerow([key, value])
        comp = self.db.latest_compliance_score("NIST-CSF") or {}
        writer.writerow(["compliance_score", comp.get("score", "-")])
        siem = self.db.siem_summary()
        writer.writerow(["siem_open_alerts", siem.get("open_alerts", 0)])
        writer.writerow(["xdr_open_findings", len(self.db.list_xdr_findings(limit=500))])
        return buf.getvalue()

    def _compliance_report(self, *, tenant_id: str) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["framework", "score", "passed", "total", "computed_at"])
        for fw in ("NIST-CSF", "ISO27001", "SOC2"):
            row = self.db.latest_compliance_score(fw) or {}
            if row:
                writer.writerow([fw, row.get("score"), row.get("passed"), row.get("total"), row.get("computed_at")])
        return buf.getvalue()

    def _incidents_report(self, *, tenant_id: str) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["incident_id", "title", "severity", "status", "assignee", "endpoint_id", "created_at"])
        for inc in self.db.list_incidents():
            writer.writerow(
                [
                    inc.get("incident_id"),
                    inc.get("title"),
                    inc.get("severity"),
                    inc.get("status"),
                    inc.get("assignee"),
                    inc.get("endpoint_id"),
                    inc.get("created_at"),
                ]
            )
        return buf.getvalue()

    def _audit_report(self, *, tenant_id: str) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["audit_id", "actor", "action", "target", "created_at"])
        for row in self.db.list_audit():
            writer.writerow([row.get("audit_id"), row.get("actor"), row.get("action"), row.get("target"), row.get("created_at")])
        return buf.getvalue()

    def _siem_report(self, *, tenant_id: str) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["alert_id", "rule_id", "title", "severity", "endpoint_id", "status", "created_at"])
        for alert in self.db.list_siem_alerts(limit=500):
            writer.writerow(
                [
                    alert.get("alert_id"),
                    alert.get("rule_id"),
                    alert.get("title"),
                    alert.get("severity"),
                    alert.get("endpoint_id"),
                    alert.get("status"),
                    alert.get("created_at"),
                ]
            )
        return buf.getvalue()

    def dashboard(self) -> dict[str, Any]:
        return {
            "module": "Mersal Reporting",
            "formats": ["csv"],
            "reports": ["executive", "compliance", "incidents", "audit", "siem"],
        }

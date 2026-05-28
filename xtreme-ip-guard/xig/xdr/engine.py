# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Mersal XDR — cross-layer detection and autonomous response."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class XdrEngine:
    """Correlates SIEM + EDR + Vuln + Suricata + AI into unified findings."""

    def __init__(self, database: "Database") -> None:
        self.db = database

    def run_correlation(self) -> dict[str, Any]:
        created = 0
        by_endpoint: dict[str, dict[str, Any]] = {}

        for alert in self.db.list_siem_alerts(limit=30, status="open"):
            ep = str(alert.get("endpoint_id") or "network")
            bucket = by_endpoint.setdefault(ep, {"siem": 0, "edr": 0, "vuln": 0, "ids": 0, "score": 0})
            bucket["siem"] += 1
            bucket["score"] += int(alert.get("severity", 0))

        for det in self.db.list_edr_detections(limit=40):
            ep = str(det.get("endpoint_id") or "unknown")
            bucket = by_endpoint.setdefault(ep, {"siem": 0, "edr": 0, "vuln": 0, "ids": 0, "score": 0})
            bucket["edr"] += 1
            bucket["score"] += int(det.get("severity", 0))

        for vuln in self.db.list_vuln_findings(limit=30, status="open"):
            if float(vuln.get("severity", 0)) < 7.0:
                continue
            ep = str(vuln.get("endpoint_id") or "unknown")
            bucket = by_endpoint.setdefault(ep, {"siem": 0, "edr": 0, "vuln": 0, "ids": 0, "score": 0})
            bucket["vuln"] += 1
            bucket["score"] += int(float(vuln["severity"]) * 10)

        for ids in self.db.list_suricata_alerts(limit=20):
            bucket = by_endpoint.setdefault("network", {"siem": 0, "edr": 0, "vuln": 0, "ids": 0, "score": 0})
            bucket["ids"] += 1
            bucket["score"] += int(ids.get("severity", 0))

        for endpoint_id, signals in by_endpoint.items():
            layers = sum(1 for k in ("siem", "edr", "vuln", "ids") if signals[k] > 0)
            if layers < 2 and signals["score"] < 80:
                continue
            severity = min(100, signals["score"] // max(layers, 1))
            sources = [k for k in ("siem", "edr", "vuln", "ids") if signals[k] > 0]
            mitre: list[str] = []
            for alert in self.db.list_siem_alerts(limit=5):
                if str(alert.get("endpoint_id")) == endpoint_id:
                    tech = (alert.get("details") or {}).get("mitre_technique")
                    if tech:
                        mitre.append(str(tech))

            action = "isolate_endpoint" if severity >= 90 else "investigate"
            finding = self.db.create_xdr_finding(
                title=f"XDR correlated threat on {endpoint_id}",
                severity=severity,
                endpoint_id=endpoint_id,
                sources=sources,
                mitre_techniques=mitre or ["T1190"],
                recommended_action=action,
                details=signals,
                confidence=min(0.99, 0.5 + layers * 0.15),
            )
            created += 1
            if action == "isolate_endpoint" and endpoint_id not in {"", "network", "unknown"}:
                self.db.set_endpoint_isolation(endpoint_id, True)

            from ..incidents import IncidentManager

            IncidentManager(self.db).sync_from_alerts(
                [
                    {
                        "alert_id": finding["finding_id"],
                        "severity": severity,
                        "endpoint_id": endpoint_id,
                        "title": finding["title"],
                        "details": {"xdr": True, "sources": sources},
                    }
                ]
            )

        return {"findings_created": created, "endpoints_analyzed": len(by_endpoint)}

    def dashboard(self) -> dict[str, Any]:
        return {
            "module": "Mersal XDR",
            "summary": self.db.xdr_summary(),
            "findings": self.db.list_xdr_findings(limit=15),
        }

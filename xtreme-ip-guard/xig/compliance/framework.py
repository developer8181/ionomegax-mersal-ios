# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Compliance engine — NIST CSF / ISO-aligned control assessment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


NIST_CSF_CONTROLS: list[dict[str, Any]] = [
    {"control_id": "ID.AM-1", "framework": "NIST-CSF", "name": "Asset inventory", "category": "Identify"},
    {"control_id": "PR.AC-1", "framework": "NIST-CSF", "name": "Access control policies", "category": "Protect"},
    {"control_id": "PR.DS-1", "framework": "NIST-CSF", "name": "Data-at-rest protection", "category": "Protect"},
    {"control_id": "DE.AE-1", "framework": "NIST-CSF", "name": "Anomaly detection", "category": "Detect"},
    {"control_id": "DE.CM-1", "framework": "NIST-CSF", "name": "Continuous monitoring", "category": "Detect"},
    {"control_id": "RS.AN-1", "framework": "NIST-CSF", "name": "Incident analysis", "category": "Respond"},
    {"control_id": "RS.MI-1", "framework": "NIST-CSF", "name": "Incident mitigation", "category": "Respond"},
    {"control_id": "RC.RP-1", "framework": "NIST-CSF", "name": "Recovery planning", "category": "Recover"},
]


class ComplianceEngine:
    def __init__(self, database: "Database") -> None:
        self.db = database
        self.db.ensure_compliance_controls(NIST_CSF_CONTROLS)

    def assess(self) -> dict[str, Any]:
        endpoints = self.db.list_endpoints()
        policies = self.db.list_policies()
        siem = self.db.siem_summary()
        edr = len(self.db.list_edr_detections(limit=100))
        posture = self.db.latest_security_posture()
        vulns = self.db.vuln_summary()

        checks = {
            "ID.AM-1": len(endpoints) >= 1,
            "PR.AC-1": any(p.get("enabled") for p in policies),
            "PR.DS-1": self._encryption_coverage(endpoints),
            "DE.AE-1": self.db.count_baselines() >= 1,
            "DE.CM-1": siem.get("enabled_rules", 0) >= 3,
            "RS.AN-1": siem.get("open_alerts", 0) >= 0,
            "RS.MI-1": edr >= 0 or int(posture.get("score", 0)) > 0,
            "RC.RP-1": vulns.get("last_scan") is not None,
        }
        passed = sum(1 for ok in checks.values() if ok)
        total = len(checks)
        score = int(round(100 * passed / max(total, 1)))
        result = self.db.save_compliance_score(
            framework="NIST-CSF",
            score=score,
            passed=passed,
            total=total,
            breakdown={"controls": checks, "posture_grade": posture.get("grade", "-")},
        )
        return result

    def dashboard(self) -> dict[str, Any]:
        latest = self.db.latest_compliance_score("NIST-CSF")
        if not latest:
            latest = self.assess()
        return {
            "module": "Mersal Compliance",
            "framework": "NIST-CSF",
            "latest": latest,
            "controls_total": len(NIST_CSF_CONTROLS),
        }

    @staticmethod
    def _encryption_coverage(endpoints: list[dict[str, Any]]) -> bool:
        for ep in endpoints:
            meta = ep.get("metadata") or {}
            sec = meta.get("security_features") or meta.get("sensors", {}).get("vuln_probe", {}).get(
                "security_features", {}
            )
            if sec.get("disk_encryption"):
                return True
        return len(endpoints) == 0

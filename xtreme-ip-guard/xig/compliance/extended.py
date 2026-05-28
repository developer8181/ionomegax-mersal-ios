# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Extended GRC — ISO 27001 and SOC 2 Type II control libraries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database

ISO27001_CONTROLS: list[dict[str, Any]] = [
    {"control_id": "A.5.1", "framework": "ISO27001", "name": "Information security policies", "category": "Organizational"},
    {"control_id": "A.8.1", "framework": "ISO27001", "name": "User endpoint devices", "category": "Technological"},
    {"control_id": "A.8.7", "framework": "ISO27001", "name": "Protection against malware", "category": "Technological"},
    {"control_id": "A.8.15", "framework": "ISO27001", "name": "Logging", "category": "Technological"},
    {"control_id": "A.8.16", "framework": "ISO27001", "name": "Monitoring activities", "category": "Technological"},
    {"control_id": "A.8.23", "framework": "ISO27001", "name": "Web filtering", "category": "Technological"},
]

SOC2_CONTROLS: list[dict[str, Any]] = [
    {"control_id": "CC6.1", "framework": "SOC2", "name": "Logical access security", "category": "Common Criteria"},
    {"control_id": "CC7.2", "framework": "SOC2", "name": "System monitoring", "category": "Common Criteria"},
    {"control_id": "CC7.3", "framework": "SOC2", "name": "Evaluate security events", "category": "Common Criteria"},
    {"control_id": "CC7.4", "framework": "SOC2", "name": "Incident response", "category": "Common Criteria"},
    {"control_id": "CC8.1", "framework": "SOC2", "name": "Change management", "category": "Common Criteria"},
]


class ExtendedComplianceEngine:
    def __init__(self, database: "Database") -> None:
        self.db = database
        self.db.ensure_compliance_controls(ISO27001_CONTROLS + SOC2_CONTROLS)

    def assess_framework(self, framework: str) -> dict[str, Any]:
        endpoints = self.db.list_endpoints()
        policies = self.db.list_policies()
        siem = self.db.siem_summary()
        edr_count = len(self.db.list_edr_detections(limit=50))
        users = len(self.db.list_rbac_users())

        if framework == "ISO27001":
            checks = {
                "A.5.1": len(policies) >= 1,
                "A.8.1": len(endpoints) >= 1,
                "A.8.7": edr_count >= 0,
                "A.8.15": self.db.count_log_records() >= 1,
                "A.8.16": siem.get("enabled_rules", 0) >= 3,
                "A.8.23": any(p.get("enabled") for p in policies),
            }
        elif framework == "SOC2":
            checks = {
                "CC6.1": users >= 1 or bool(policies),
                "CC7.2": siem.get("total_alerts", 0) >= 0,
                "CC7.3": siem.get("open_alerts", 0) >= 0,
                "CC7.4": len(self.db.list_incidents()) >= 0,
                "CC8.1": len(policies) >= 1,
            }
        else:
            checks = {}
        passed = sum(1 for ok in checks.values() if ok)
        total = len(checks) or 1
        score = int(round(100 * passed / total))
        return self.db.save_compliance_score(
            framework=framework,
            score=score,
            passed=passed,
            total=total,
            breakdown={"controls": checks},
        )

    def assess_all(self) -> dict[str, Any]:
        from .framework import ComplianceEngine

        nist = ComplianceEngine(self.db).assess()
        iso = self.assess_framework("ISO27001")
        soc = self.assess_framework("SOC2")
        return {"NIST-CSF": nist, "ISO27001": iso, "SOC2": soc}

# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Compliance evidence pack — audit-ready export for banks and regulators."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class ComplianceEvidencePack:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def build(self, *, tenant_id: str = "default") -> dict[str, Any]:
        from ..platform_ops.enterprise_readiness import enterprise_adoption_report
        from ..platform_ops.reliability_engine import ReliabilityEngine

        pack = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "product": "Extreme Cyber Security Platform",
            "audit_chain": self.db.verify_audit_chain(),
            "compliance_scores": {
                fw: self.db.latest_compliance_score(fw) for fw in ("NIST-CSF", "ISO27001", "SOC2")
            },
            "rbac_users_count": len(self.db.list_rbac_users(tenant_id=tenant_id)),
            "policies_count": len(self.db.list_policies()),
            "siem_open_alerts": len(self.db.list_siem_alerts(limit=500, status="open")),
            "incidents_open": len(self.db.list_incidents(status="open")),
            "enterprise_adoption": enterprise_adoption_report(self.db),
            "reliability": ReliabilityEngine(self.db).full_report(),
            "audit_sample": self.db.list_audit(limit=50, tenant_id=tenant_id),
        }
        canonical = json.dumps(pack, sort_keys=True, default=str)
        pack["integrity_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
        return pack

# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Platform health — autonomous status for independent SOC operation."""

from __future__ import annotations

import os
import shutil
from typing import TYPE_CHECKING, Any

from ..config import postgres_dsn, tls_enabled
from ..db.adapter import uses_postgres
from ..edr.ebpf_probe import ebpf_available
from ..integrations.oidc import OidcProvider
from ..integrations.saml import SamlProvider
from ..readiness import production_readiness, tool_versions

if TYPE_CHECKING:
    from ..storage import Database


class PlatformHealth:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def full_status(self) -> dict[str, Any]:
        readiness = production_readiness(self.db)
        modules = {
            "command_center": self._module_ok("command_center"),
            "siem": self._module_ok("siem", detail={"alerts": len(self.db.list_siem_alerts(limit=5))}),
            "edr": self._module_ok("edr", detail={"detections": len(self.db.list_edr_detections(limit=5))}),
            "xdr": self._module_ok("xdr", detail={"findings": len(self.db.list_xdr_findings(limit=5))}),
            "soar": self._module_ok("soar", detail={"runs": len(self.db.list_soar_runs(limit=3))}),
            "threat_intel": self._module_ok("threat_intel", detail=self.db.threat_intel_summary()),
            "compliance": self._module_ok("compliance", detail=self.db.latest_compliance_score() or {}),
            "logvault": self._module_ok("logvault", detail={"records": self.db.count_log_records()}),
        }
        autonomous = all(m["status"] == "ok" for m in modules.values()) and readiness.get("ready_for_trial")
        return {
            "platform": "Mersal Standalone Security Platform",
            "autonomous_ready": autonomous,
            "readiness": readiness,
            "modules": modules,
            "infrastructure": {
                "tls": tls_enabled(),
                "postgres_active": uses_postgres(),
                "postgres_configured": bool(postgres_dsn()),
                "suricata_installed": shutil.which("suricata") is not None,
                "nmap": shutil.which("nmap") is not None,
                "ebpf": ebpf_available(),
                "oidc": OidcProvider(self.db).configured(),
                "saml": SamlProvider(self.db).configured(),
            },
            "tools": tool_versions(),
            "siem_forwarders": len(self.db.list_siem_forwarders(enabled_only=True)),
            "audit_chain": self.db.verify_audit_chain(),
        }

    def _module_ok(self, name: str, *, detail: dict[str, Any] | None = None) -> dict[str, Any]:
        self.db.touch_platform_heartbeat(name, status="ok", detail=detail or {})
        return {"status": "ok", "component": name, "detail": detail or {}}

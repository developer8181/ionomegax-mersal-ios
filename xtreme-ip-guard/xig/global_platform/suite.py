# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Orchestrates v6 global capabilities atop Enterprise Suite."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .. import __version__
from ..compliance.extended import ExtendedComplianceEngine
from ..rbac import RbacEngine
from ..reporting import ReportExporter
from ..siem.window_correlator import WindowCorrelator
from ..soar.webhooks import WebhookDispatcher
from ..tenant import TenantManager
from ..threat_feeds.taxii import TaxiiClient

if TYPE_CHECKING:
    from ..enterprise.suite import MersalEnterpriseSuite
    from ..storage import Database


class MersalGlobalPlatform:
    def __init__(self, database: "Database", enterprise: "MersalEnterpriseSuite | None" = None) -> None:
        self.db = database
        self.enterprise = enterprise
        self.tenants = TenantManager(database)
        self.rbac = RbacEngine(database)
        self.windows = WindowCorrelator(database)
        self.taxii = TaxiiClient(database)
        self.reports = ReportExporter(database)
        self.webhooks = WebhookDispatcher(database)
        self.grc = ExtendedComplianceEngine(database)

    def run_global_cycle(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        if self.enterprise:
            results["enterprise"] = self.enterprise.run_enterprise_cycle()
        results["window_siem"] = self.windows.run_retrospective(limit=150)
        results["grc"] = self.grc.assess_all()
        results["taxii"] = self.taxii.sync()
        results["webhooks_ping"] = self.webhooks.dispatch(
            "platform.cycle",
            {"status": "completed", "version": __version__},
        )
        return results

    def comparison_matrix(self) -> list[dict[str, str]]:
        base = self.enterprise.comparison_matrix() if self.enterprise else []
        extra = [
            {"capability": "Multi-tenant / MSP", "mersal": "Tenant isolation + plans", "legacy": "Sentinel workspaces"},
            {"capability": "RBAC / SSO-ready", "mersal": "4 SOC roles + API tokens", "legacy": "Entra ID / Splunk roles"},
            {"capability": "SIEM window rules", "mersal": "Sliding-window correlation", "legacy": "Splunk ES / Sentinel fusion"},
            {"capability": "TAXII 2.0", "mersal": "STIX poll + CISA KEV", "legacy": "Commercial TI feeds"},
            {"capability": "GRC", "mersal": "NIST + ISO27001 + SOC2", "legacy": "ServiceNow GRC"},
            {"capability": "Reporting", "mersal": "CSV executive + SOC exports", "legacy": "PDF board packs"},
            {"capability": "SOAR webhooks", "mersal": "Signed outbound integrations", "legacy": "XSOAR / Logic Apps"},
            {"capability": "Live alert stream", "mersal": "SSE to Command Center", "legacy": "Splunk streaming"},
        ]
        return base + extra

    def dashboard(self) -> dict[str, Any]:
        return {
            "platform": "Extreme Cyber Security Global Platform",
            "version": __version__,
            "tier": "global_alternative_integrated",
            "tenants": self.tenants.dashboard(),
            "rbac": self.rbac.dashboard(),
            "reporting": self.reports.dashboard(),
            "window_siem": {"rules": len(self.db.list_window_rules())},
            "grc_frameworks": ["NIST-CSF", "ISO27001", "SOC2"],
            "enterprise": self.enterprise.dashboard() if self.enterprise else {},
        }

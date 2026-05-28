# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Unified platform — single control plane for fully integrated Mersal operations."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from .. import __version__
from ..integrations.integration_hub import IntegrationHub
from ..platform_ops.backup import BackupManager
from ..platform_ops.enterprise_readiness import enterprise_adoption_report
from ..platform_ops.health import PlatformHealth
from ..compliance.evidence_pack import ComplianceEvidencePack
from ..platform_ops.standalone import StandaloneController

if TYPE_CHECKING:
    from ..fabric import MersalSecurityFabric
    from ..storage import Database


class UnifiedPlatformController:
    """Orchestrates the complete integrated security platform."""

    def __init__(self, database: "Database", fabric: "MersalSecurityFabric | None" = None) -> None:
        self.db = database
        self.fabric = fabric

    def full_dashboard(self) -> dict[str, Any]:
        health = PlatformHealth(self.db).full_status()
        hub = IntegrationHub(self.db).full_matrix()
        adoption = enterprise_adoption_report(self.db)
        from .global_alternative import _parity_index, _parity_tier, parity_matrix
        from .reliability_engine import ReliabilityEngine

        reliability = ReliabilityEngine(self.db).full_report()
        matrix = parity_matrix()
        parity_idx = _parity_index(matrix)
        parity_tier = _parity_tier(parity_idx)
        modules = {
            "siem": {
                "alerts_open": len(self.db.list_siem_alerts(limit=500, status="open")),
                "rules": len(self.db.list_window_rules()),
            },
            "xdr": self.db.xdr_summary() if hasattr(self.db, "xdr_summary") else {},
            "edr": {"detections": len(self.db.list_edr_detections(limit=100))},
            "vuln": self.db.vuln_summary(),
            "soar": self.db.soar_summary(),
            "compliance": self.db.latest_compliance_score() or {},
            "threat_intel": self.db.threat_intel_summary(),
            "endpoints": len(self.db.list_endpoints()),
            "agents": len(self.db.list_agents()),
        }
        return {
            "platform": "Extreme Cyber Security Unified Platform",
            "version": __version__,
            "integration_complete": adoption.get("ready_for_large_institution", False),
            "global_alternative_ready": (
                parity_idx >= 75
                and adoption.get("ready_for_large_institution", False)
                and reliability.get("dependable_for_operations", False)
            ),
            "parity_index": parity_idx,
            "parity_tier": parity_tier,
            "dependable_operations": reliability.get("dependable_for_operations", False),
            "trust_score": reliability.get("trust_score"),
            "sla_tier": reliability.get("sla_tier"),
            "tier": adoption.get("tier"),
            "adoption_percent": adoption.get("percent"),
            "reliability": reliability,
            "health": health,
            "integration_hub": hub,
            "enterprise_adoption": adoption,
            "modules": modules,
            "global_alternative": {
                "parity_index": parity_idx,
                "parity_tier": parity_tier,
                "ready_as_global_alternative": (
                    parity_idx >= 75
                    and adoption.get("ready_for_large_institution", False)
                    and reliability.get("dependable_for_operations", False)
                ),
                "matrix_api": "/api/platform/global-alternative/matrix",
            },
            "capabilities": [
                "siem",
                "xdr",
                "soar",
                "edr",
                "vuln",
                "threat_intel",
                "compliance",
                "logvault",
                "suricata",
                "oidc",
                "saml",
                "scim",
                "agent_edr_ebpf",
                "signed_updates",
                "postgres_ha",
                "autonomous_soc",
                "global_alternative_mode",
            ],
        }

    def run_complete_cycle(self) -> dict[str, Any]:
        results: dict[str, Any] = {"version": __version__}
        if self.fabric:
            results["autonomous"] = StandaloneController(self.db, self.fabric).run_autonomous_cycle()
            results["fabric_daily"] = self.fabric.scheduler.run_daily_cycle()
        else:
            from ..fabric.scheduler import SecurityScheduler

            sched = SecurityScheduler(self.db, fabric=None)
            results["fabric_daily"] = sched.run_daily_cycle()
        results["backup"] = BackupManager(self.db).create_backup()
        from .reliability_engine import ReliabilityEngine

        rel = ReliabilityEngine(self.db)
        results["reliability"] = rel.full_report()
        results["stale_agent_alerts"] = rel.raise_stale_agent_alerts()
        results["posture"] = self.db.latest_security_posture()
        pack = ComplianceEvidencePack(self.db).build()
        results["evidence_pack"] = {
            "integrity_sha256": pack["integrity_sha256"],
            "generated_at": pack["generated_at"],
        }
        self.db.touch_platform_heartbeat(
            "unified_platform",
            status="ok",
            detail={"cycle": "complete", "version": __version__},
        )
        return results

    def bootstrap_enterprise(self, *, tenant_id: str = "default") -> dict[str, Any]:
        """One-shot enterprise bootstrap — policies, intel, SIEM, compliance baselines."""
        steps: dict[str, Any] = {}
        self.db.init_schema()
        self.db.ensure_rbac_seed()
        if hasattr(self.db, "ensure_soar_playbooks"):
            self.db.ensure_soar_playbooks()
        if hasattr(self.db, "ensure_window_rules"):
            from ..siem.window_correlator import DEFAULT_WINDOW_RULES

            steps["window_rules"] = self.db.ensure_window_rules(DEFAULT_WINDOW_RULES)
        steps["threat_intel"] = len(self.db.list_threat_intel())
        if steps["threat_intel"] < 5:
            from ..threat_feeds import ThreatFeedSync

            steps["threat_sync"] = ThreatFeedSync(self.db).sync_all()
        siem_host = os.environ.get("MERSAL_SIEM_FORWARD_HOST", "").strip()
        if siem_host and not self.db.list_siem_forwarders(enabled_only=False):
            import secrets

            fw = self.db.create_siem_forwarder(
                forwarder_id=f"fw-{secrets.token_hex(6)}",
                name="default-siem",
                host=siem_host,
                port=int(os.environ.get("MERSAL_SIEM_FORWARD_PORT", "514")),
                protocol=os.environ.get("MERSAL_SIEM_FORWARD_PROTOCOL", "syslog_udp"),
                tenant_id=tenant_id,
            )
            steps["siem_forwarder"] = fw.get("forwarder_id")
        steps["endpoints"] = len(self.db.list_endpoints())
        steps["policies"] = len(self.db.list_policies())
        steps["adoption"] = enterprise_adoption_report(self.db)
        self.db.record_audit(
            "bootstrap",
            "platform.bootstrap_enterprise",
            target=tenant_id,
            tenant_id=tenant_id,
            details={"steps": list(steps.keys())},
        )
        return {"ok": True, "tenant_id": tenant_id, "steps": steps}

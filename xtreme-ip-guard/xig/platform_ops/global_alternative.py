# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Global alternative platform — unified parity vs world-class vendor stacks."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from .. import __version__
from ..brand import BRAND
from ..compliance.evidence_pack import ComplianceEvidencePack
from ..integrations.integration_hub import IntegrationHub
from ..platform_ops.enterprise_readiness import enterprise_adoption_report
from ..platform_ops.reliability_engine import ReliabilityEngine
from ..platform_ops.unified_platform import UnifiedPlatformController

if TYPE_CHECKING:
    from ..fabric import MersalSecurityFabric
    from ..storage import Database

PLATFORM_LINEAGE = "8.9.0"

_PARITY_WEIGHTS = {"full": 1.0, "strong": 0.85, "partial": 0.55, "roadmap": 0.2}


def parity_matrix() -> list[dict[str, Any]]:
    """Capability map: ECS vs CrowdStrike / Sentinel / Splunk / Palo Alto class stacks."""
    rows = [
        _row(
            "Unified XDR + SIEM + SOAR",
            "Single control plane & APIs",
            "Falcon + LogScale add-ons",
            "Sentinel + Defender XDR",
            "Splunk ES + SOAR",
            "Cortex XDR + XSOAR",
            "full",
        ),
        _row(
            "Bilingual SOC console",
            "Command Center AR/EN RTL",
            "English-first portal",
            "Azure portal",
            "Splunk Web",
            "Cortex console",
            "full",
        ),
        _row(
            "Endpoint telemetry",
            "Agent: process, network, FIM, YARA",
            "Kernel sensor cloud",
            "Defender sensor",
            "UBA add-ons",
            "Traps agent",
            "strong",
        ),
        _row(
            "eBPF / kernel visibility",
            "bpftool program inspection",
            "Custom kernel drivers",
            "Limited on Linux",
            "N/A typical",
            "Linux sensor",
            "partial",
        ),
        _row(
            "SIEM correlation",
            "Rules + sliding windows + MITRE",
            "IOC + analytics cloud",
            "Fusion + KQL",
            "SPL + ES",
            "Analytics",
            "strong",
        ),
        _row(
            "SOAR automation",
            "Playbooks + webhooks + isolate",
            "RTR + workflows",
            "Logic Apps / Sentinel SOAR",
            "Phantom / SOAR",
            "XSOAR",
            "strong",
        ),
        _row(
            "Threat intelligence",
            "STIX/TAXII + CISA KEV local",
            "Global cloud TI",
            "Microsoft TI",
            "Threat intel modular",
            "Unit 42 feeds",
            "strong",
        ),
        _row(
            "Vulnerability management",
            "Scheduled scans + KEV priority",
            "Spotlight",
            "Defender VM",
            "VR add-on",
            "Cortex Xpanse",
            "strong",
        ),
        _row(
            "GRC / compliance",
            "NIST · ISO27001 · SOC2 live",
            "Limited native",
            "Regulatory templates",
            "GRC apps",
            "Compliance svc",
            "full",
        ),
        _row(
            "Identity (SSO)",
            "OIDC + SAML verify",
            "SSO partners",
            "Entra ID native",
            "SAML/OIDC",
            "IdP federation",
            "strong",
        ),
        _row(
            "User provisioning",
            "SCIM 2.0 lifecycle",
            "SCIM partners",
            "Entra provisioning",
            "Manual / apps",
            "AD sync",
            "strong",
        ),
        _row(
            "Multi-tenant SOC",
            "tenant_id + RBAC roles",
            "Parent/child CID",
            "Workspaces",
            "Index per tenant",
            "Multi-tenant",
            "full",
        ),
        _row(
            "Log management",
            "Log Vault search + ingest",
            "LogScale",
            "Log Analytics",
            "Splunk core",
            "Logging service",
            "strong",
        ),
        _row(
            "Network IDS",
            "Suricata eve.json ingest",
            "N/A",
            "NDR partners",
            "IDS apps",
            "NGFW + IDS",
            "partial",
        ),
        _row(
            "Backup & DR",
            "Encrypted backup/restore API",
            "Cloud retain",
            "Azure backup",
            "Index backup",
            "Panorama backup",
            "full",
        ),
        _row(
            "PostgreSQL HA",
            "Primary + replica health",
            "SaaS only",
            "Azure SQL",
            "Indexer clusters",
            "Varies",
            "strong",
        ),
        _row(
            "Signed agent updates",
            "Manifest channel + verify",
            "Cloud delivery",
            "Defender updates",
            "Deployment server",
            "Content updates",
            "full",
        ),
        _row(
            "Audit & evidence",
            "Hash chain + evidence pack",
            "Audit APIs",
            "Activity logs",
            "Audit framework",
            "Audit logs",
            "full",
        ),
        _row(
            "Autonomous SOC cycle",
            "Scheduler + complete-cycle API",
            "Managed hunting",
            "Automation rules",
            "SOAR scheduled",
            "Playbook jobs",
            "strong",
        ),
        _row(
            "Hyperscale cloud TI mesh",
            "Self-hosted feeds",
            "Global cloud",
            "Microsoft cloud",
            "Splunk cloud",
            "Unit 42 cloud",
            "partial",
        ),
        _row(
            "24×7 managed MSSP",
            "Self-hosted — your SOC",
            "CrowdStrike Complete",
            "Microsoft SOC",
            "MSS partners",
            "Unit 42 retainer",
            "roadmap",
        ),
    ]
    return rows


class GlobalAlternativeController:
    """Orchestrates world-class integrated mode on customer infrastructure."""

    def __init__(self, database: "Database", fabric: "MersalSecurityFabric | None" = None) -> None:
        self.db = database
        self.fabric = fabric

    def summary(self) -> dict[str, Any]:
        matrix = parity_matrix()
        index = _parity_index(matrix)
        adoption = enterprise_adoption_report(self.db)
        reliability = ReliabilityEngine(self.db).full_report()
        hub = IntegrationHub(self.db).full_matrix()
        ready = (
            index >= 75
            and adoption.get("ready_for_large_institution", False)
            and reliability.get("dependable_for_operations", False)
        )
        return {
            "product": BRAND["full_name"],
            "version": __version__,
            "platform_lineage": PLATFORM_LINEAGE,
            "positioning": "integrated_global_alternative",
            "tagline_en": BRAND["tagline_en"],
            "tagline_ar": BRAND["tagline_ar"],
            "parity_index": index,
            "parity_tier": _parity_tier(index),
            "ready_as_global_alternative": ready,
            "matrix_rows": len(matrix),
            "matrix_full_count": sum(1 for r in matrix if r["parity"] == "full"),
            "matrix_strong_count": sum(1 for r in matrix if r["parity"] == "strong"),
            "enterprise_adoption": {
                "tier": adoption.get("tier"),
                "percent": adoption.get("percent"),
                "ready_for_large_institution": adoption.get("ready_for_large_institution"),
            },
            "reliability": {
                "trust_score": reliability.get("trust_score"),
                "sla_tier": reliability.get("sla_tier"),
                "dependable_for_operations": reliability.get("dependable_for_operations"),
            },
            "integration_hub_tier": hub.get("tier"),
            "modules_linked": hub.get("modules_linked", []),
            "deployment_model": "self_hosted_sovereign",
            "honest_limits": [
                "Kernel EDR depth varies by OS — not a licensed CrowdStrike sensor binary.",
                "Log volume at national scale requires Postgres/cluster sizing and SIEM export.",
                "MSSP 24×7 operations are customer-run unless a partner SOC is engaged.",
            ],
            "activate_api": "/api/platform/global-alternative/activate",
            "matrix_api": "/api/platform/global-alternative/matrix",
        }

    def activate(self, *, tenant_id: str = "default") -> dict[str, Any]:
        """One-shot: bootstrap enterprise + full SOC cycle + evidence + global cycle."""
        steps: dict[str, Any] = {}
        ctrl = UnifiedPlatformController(self.db, self.fabric)
        steps["bootstrap"] = ctrl.bootstrap_enterprise(tenant_id=tenant_id)
        steps["complete_cycle"] = ctrl.run_complete_cycle()
        steps["reliability_scan"] = ReliabilityEngine(self.db).raise_stale_agent_alerts()
        if self.fabric:
            steps["global_cycle"] = self.fabric.global_platform.run_global_cycle()
            steps["xdr_soar"] = self._xdr_soar_bridge()
        pack = ComplianceEvidencePack(self.db).build(tenant_id=tenant_id)
        steps["evidence_pack"] = {
            "integrity_sha256": pack["integrity_sha256"],
            "generated_at": pack["generated_at"],
        }
        summary = self.summary()
        self.db.record_audit(
            "platform",
            "global_alternative.activate",
            target=tenant_id,
            tenant_id=tenant_id,
            details={
                "parity_index": summary["parity_index"],
                "ready": summary["ready_as_global_alternative"],
            },
        )
        return {"ok": True, "tenant_id": tenant_id, "summary": summary, "steps": steps}

    def _xdr_soar_bridge(self) -> dict[str, Any]:
        if not self.fabric:
            return {"skipped": True}
        from ..xdr.soar_bridge import XdrSoarBridge

        return XdrSoarBridge(self.db, self.fabric.soar).execute_for_findings(limit=20)


def _row(
    capability: str,
    ecs: str,
    crowdstrike: str,
    sentinel: str,
    splunk: str,
    palo_alto: str,
    parity: str,
) -> dict[str, Any]:
    return {
        "capability": capability,
        "ecs": ecs,
        "vendors": {
            "crowdstrike": crowdstrike,
            "microsoft_sentinel": sentinel,
            "splunk": splunk,
            "palo_alto": palo_alto,
        },
        "parity": parity,
    }


def _parity_index(matrix: list[dict[str, Any]]) -> int:
    if not matrix:
        return 0
    total = sum(_PARITY_WEIGHTS.get(r["parity"], 0.2) for r in matrix)
    return int(100 * total / len(matrix))


def _parity_tier(index: int) -> str:
    if index >= 88:
        return "global_alternative"
    if index >= 75:
        return "enterprise_integrated"
    if index >= 60:
        return "pilot_unified"
    return "evaluation"


def recommended_production_env() -> dict[str, str]:
    """Checklist for operators targeting global-alternative tier."""
    return {
        "MERSAL_PRODUCTION": "1",
        "MERSAL_ENTERPRISE": "1",
        "MERSAL_ENTERPRISE_STRICT": "1",
        "MERSAL_POSTGRES_DSN": "postgresql://user:pass@host:5432/mersal",
        "MERSAL_TLS_CERT": "/path/to/cert.pem",
        "MERSAL_TLS_KEY": "/path/to/key.pem",
        "MERSAL_UPDATE_SIGNING_KEY": "openssl rand -hex 32",
        "MERSAL_AUTONOMOUS": "1",
        "MERSAL_OIDC_ISSUER": "https://idp.example.com",
        "MERSAL_SIEM_FORWARD_HOST": "siem.example.com",
    }

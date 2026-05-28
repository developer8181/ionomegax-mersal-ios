# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Advanced reliability engine — SLA metrics, stale agents, operational trust score."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

from .. import __version__
from ..config import enterprise_strict, is_enterprise, is_production, tls_enabled
from ..db.adapter import uses_postgres
from ..platform_ops.backup import BackupManager
from ..integrations.integration_hub import IntegrationHub
from ..platform_ops.postgres_health import postgres_cluster_health

if TYPE_CHECKING:
    from ..storage import Database


class ReliabilityEngine:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def full_report(self) -> dict[str, Any]:
        stale_seconds = int(os.environ.get("MERSAL_AGENT_STALE_SECONDS", "300"))
        stale = self.db.list_stale_agents(threshold_seconds=stale_seconds)
        agents = self.db.list_agents()
        backup = BackupManager(self.db).health()
        pg = postgres_cluster_health()
        audit = self.db.verify_audit_chain()
        sched = self.db.scheduler_summary()
        sched_ok = _scheduler_recent(sched)
        siem_ok = _siem_forward_recent(self.db)
        hub = IntegrationHub(self.db).full_matrix()

        checks = [
            _check("audit_chain", audit.get("valid", False), "Tamper-evident audit log"),
            _check("backup_fresh", backup.get("ok", False), "Recent platform backup"),
            _check("postgres_ok", pg.get("ok", True) if uses_postgres() else True, "PostgreSQL cluster"),
            _check("no_stale_agents", len(stale) == 0, f"All agents seen within {stale_seconds}s"),
            _check("tls_when_strict", tls_enabled() or not enterprise_strict(), "TLS for strict enterprise"),
            _check("production_mode", is_production(), "MERSAL_PRODUCTION=1"),
            _check("scheduler_active", sched_ok, "Security scheduler ran within 48h"),
            _check(
                "enterprise_profile",
                is_enterprise() and is_production(),
                "Enterprise + production profile",
            ),
            _check("integration_fabric", len(hub.get("modules_linked", [])) >= 6, "Integration fabric modules"),
            _check("siem_export_ready", siem_ok, "SIEM forwarders or recent export cursor"),
        ]

        passed = sum(1 for c in checks if c["ok"])
        trust_score = int(100 * passed / max(len(checks), 1))
        sla_tier = "gold" if trust_score >= 90 else "silver" if trust_score >= 75 else "bronze"

        report = {
            "version": __version__,
            "trust_score": trust_score,
            "sla_tier": sla_tier,
            "checks_passed": passed,
            "checks_total": len(checks),
            "checks": checks,
            "agents": {
                "total": len(agents),
                "stale": len(stale),
                "stale_threshold_seconds": stale_seconds,
                "stale_agents": stale[:20],
            },
            "backup": backup,
            "postgres": pg,
            "audit_chain": audit,
            "enterprise_mode": is_enterprise(),
            "dependable_for_operations": trust_score >= 75 and audit.get("valid", False),
        }
        self.db.set_platform_setting(
            "reliability_last_report",
            json.dumps({"trust_score": trust_score, "sla_tier": sla_tier}, sort_keys=True),
        )
        return report

    def raise_stale_agent_alerts(self) -> dict[str, Any]:
        stale_seconds = int(os.environ.get("MERSAL_AGENT_STALE_SECONDS", "300"))
        created = 0
        for agent in self.db.list_stale_agents(threshold_seconds=stale_seconds):
            agent_id = str(agent.get("agent_id", ""))
            hostname = str(agent.get("hostname", agent_id))
            if self._has_open_stale_alert(agent_id):
                continue
            self.db.create_siem_alert(
                rule_id="RELIABILITY-STALE-AGENT",
                title=f"Stale agent: {hostname}",
                severity=72,
                endpoint_id=str((agent.get("metadata") or {}).get("endpoint_id", agent_id)),
                details={"agent_id": agent_id, "last_seen": agent.get("last_seen"), "type": "reliability"},
            )
            created += 1
        return {"alerts_created": created}

    def _has_open_stale_alert(self, agent_id: str) -> bool:
        for alert in self.db.list_siem_alerts(limit=30, status="open"):
            det = alert.get("details") or {}
            if det.get("type") == "reliability" and det.get("agent_id") == agent_id:
                return True
        return False


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "detail": detail}


def _scheduler_recent(summary: dict[str, Any]) -> bool:
    from datetime import datetime, timezone

    jobs = summary.get("recent_jobs") or []
    if not jobs:
        return True
    latest = jobs[0].get("created_at")
    if not latest:
        return False
    try:
        if isinstance(latest, str):
            ts = datetime.fromisoformat(latest.replace("Z", "+00:00"))
        else:
            ts = latest
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).total_seconds()
        return age < 172800
    except (TypeError, ValueError):
        return False


def _siem_forward_recent(database: "Database") -> bool:
    if not database.list_siem_forwarders(enabled_only=False):
        return True
    if database.list_siem_forwarders(enabled_only=True):
        return True
    raw = database.get_platform_setting("siem_forward_cursor", "{}")
    try:
        cursor = json.loads(raw)
    except json.JSONDecodeError:
        return False
    return bool(cursor)

# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Enterprise readiness scorecard — adoption tier for large institutions."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

from ..config import enterprise_strict, is_enterprise, is_production, postgres_dsn, tls_enabled
from ..db.adapter import uses_postgres
from ..integrations.integration_hub import IntegrationHub
from ..integrations.oidc import OidcProvider
from ..integrations.saml import SamlProvider
from ..platform_ops.backup import BackupManager
from ..platform_ops.postgres_health import postgres_cluster_health
from ..readiness import production_readiness
from ..security.access import organization_startup_errors

if TYPE_CHECKING:
    from ..storage import Database


def enterprise_adoption_report(database: "Database") -> dict[str, Any]:
    base = production_readiness(database)
    hub = IntegrationHub(database).full_matrix()
    pg = postgres_cluster_health()
    backup = BackupManager(database).health()
    startup_errors = organization_startup_errors()
    from .reliability_engine import ReliabilityEngine

    reliability = ReliabilityEngine(database).full_report()

    criteria = [
        _criterion("production_mode", is_production(), 10, required=True),
        _criterion("enterprise_profile", is_enterprise(), 10, required=True),
        _criterion("startup_clean", len(startup_errors) == 0, 10, required=True),
        _criterion("postgres_ha", uses_postgres() and pg.get("ok"), 15, required=False),
        _criterion("tls_enabled", tls_enabled(), 10, required=False),
        _criterion("backup_fresh", backup.get("ok", False), 10, required=False),
        _criterion("sso_configured", OidcProvider(database).configured() or SamlProvider(database).configured(), 10, required=False),
        _criterion("siem_export", len(database.list_siem_forwarders(enabled_only=True)) >= 1, 10, required=False),
        _criterion("integration_fabric", len(hub.get("modules_linked", [])) >= 6, 5, required=False),
        _criterion("dedicated_update_key", bool(os.environ.get("MERSAL_UPDATE_SIGNING_KEY", "").strip()), 10, required=False),
        _criterion(
            "reliability_trust",
            reliability.get("dependable_for_operations", False),
            10,
            required=False,
        ),
    ]

    score = sum(c["points"] for c in criteria if c["ok"])
    max_score = sum(c["points"] for c in criteria)
    tier = _tier(score, max_score, enterprise_strict())

    return {
        "version": base.get("version"),
        "tier": tier,
        "score": score,
        "max_score": max_score,
        "percent": round(100 * score / max_score, 1) if max_score else 0,
        "ready_for_large_institution": (
            tier in {"production", "regulated"}
            and len(startup_errors) == 0
            and reliability.get("dependable_for_operations", False)
        ),
        "reliability": {
            "trust_score": reliability.get("trust_score"),
            "sla_tier": reliability.get("sla_tier"),
        },
        "enterprise_strict": enterprise_strict(),
        "startup_errors": startup_errors,
        "criteria": criteria,
        "postgres": pg,
        "backup": backup,
        "integration_hub": hub,
        "base_readiness": base,
        "recommendations": _recommendations(criteria, pg, backup),
    }


def _criterion(name: str, ok: bool, points: int, *, required: bool) -> dict[str, Any]:
    return {"name": name, "ok": ok, "points": points if ok else 0, "max_points": points, "required": required}


def _tier(score: int, max_score: int, strict: bool) -> str:
    pct = (100 * score / max_score) if max_score else 0
    if strict and pct >= 85:
        return "regulated"
    if pct >= 75:
        return "production"
    if pct >= 50:
        return "pilot"
    return "evaluation"


def _recommendations(criteria: list[dict[str, Any]], pg: dict[str, Any], backup: dict[str, Any]) -> list[str]:
    tips: list[str] = []
    by_name = {c["name"]: c for c in criteria}
    if not by_name.get("postgres_ha", {}).get("ok"):
        tips.append("Configure MERSAL_POSTGRES_DSN and optional MERSAL_PG_REPLICA_DSN for HA.")
    if not by_name.get("tls_enabled", {}).get("ok"):
        tips.append("Enable TLS (MERSAL_TLS_CERT / MERSAL_TLS_KEY) for Command Center.")
    if not backup.get("ok"):
        tips.append("Run platform backup or enable scheduled backup job.")
    if not by_name.get("sso_configured", {}).get("ok"):
        tips.append("Configure OIDC or SAML for workforce SSO.")
    if not by_name.get("dedicated_update_key", {}).get("ok"):
        tips.append("Set MERSAL_UPDATE_SIGNING_KEY separate from API token.")
    if pg.get("replica_configured") and pg.get("replication_lag_seconds", 0) and pg["replication_lag_seconds"] > 30:
        tips.append("PostgreSQL replica lag exceeds 30s — investigate replication.")
    return tips

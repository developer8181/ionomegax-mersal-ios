# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Unified integration status — enterprise SOC control plane."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

from ..config import enterprise_strict, postgres_dsn, tls_enabled
from ..db.adapter import uses_postgres
from ..platform_ops.backup import BackupManager
from ..platform_ops.postgres_health import postgres_cluster_health
from ..platform_ops.updates import UpdateChannel
from .oidc import OidcProvider
from .saml import SamlProvider
from .scim import ScimProvisioner

if TYPE_CHECKING:
    from ..storage import Database


class IntegrationHub:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def full_matrix(self) -> dict[str, Any]:
        oidc = OidcProvider(self.db)
        saml = SamlProvider(self.db)
        forwarders = self.db.list_siem_forwarders(enabled_only=True)
        cursor_raw = self.db.get_platform_setting("siem_forward_cursor", "{}")
        try:
            cursor = json.loads(cursor_raw)
        except json.JSONDecodeError:
            cursor = {}
        autonomous = os.environ.get("MERSAL_AUTONOMOUS", "1").strip().lower() not in {"0", "false"}
        backup_health = BackupManager(self.db).health()
        manifest = UpdateChannel(self.db).latest_for("agent")
        updates_ok = bool(manifest and UpdateChannel(self.db).verify_manifest(manifest))
        return {
            "platform": "Extreme Cyber Security Integration Fabric",
            "tier": "enterprise-reliability",
            "enterprise_strict": enterprise_strict(),
            "identity": {
                "oidc": {
                    "configured": oidc.configured(),
                    "strict_jwt": _oidc_strict(),
                    "group_role_map": bool(os.environ.get("MERSAL_GROUP_ROLE_MAP", "").strip()),
                },
                "saml": {
                    "configured": saml.configured(),
                    "strict": os.environ.get("MERSAL_SAML_STRICT", "1") not in {"0", "false"},
                    "idp_cert": bool(os.environ.get("MERSAL_SAML_IDP_CERT", "").strip()),
                },
                "scim": {
                    "token_env": bool(os.environ.get("MERSAL_SCIM_TOKEN", "").strip()),
                    "users": len(self.db.list_rbac_users()),
                },
                "ldap": bool(os.environ.get("MERSAL_LDAP_URL", "").strip()),
            },
            "data_plane": {
                "postgres_active": uses_postgres(),
                "postgres_configured": bool(postgres_dsn()),
                "postgres_cluster": postgres_cluster_health(),
                "tls": tls_enabled(),
                "siem_forwarders": len(forwarders),
                "siem_forward_cursor": cursor,
                "backup": backup_health,
            },
            "operations": {
                "autonomous_enabled": autonomous,
                "scheduler_jobs": _scheduler_jobs(autonomous),
                "agent_updates": {"latest_manifest_ok": updates_ok, "version": (manifest or {}).get("version")},
            },
            "modules_linked": [
                "siem",
                "xdr",
                "soar",
                "edr",
                "vuln",
                "suricata",
                "threat_intel",
                "compliance",
            ],
        }

    def probe(self, integration_id: str) -> dict[str, Any]:
        if integration_id == "backup":
            return BackupManager(self.db).health()
        if integration_id == "updates":
            manifest = UpdateChannel(self.db).latest_for("agent")
            return {
                "ok": bool(manifest and UpdateChannel(self.db).verify_manifest(manifest)),
                "manifest": manifest,
            }
        if integration_id == "saml":
            return {
                "configured": SamlProvider(self.db).configured(),
                "strict": os.environ.get("MERSAL_SAML_STRICT", "1") not in {"0", "false"},
            }
        if integration_id == "postgres":
            return postgres_cluster_health()
        if integration_id == "enterprise":
            from ..platform_ops.enterprise_readiness import enterprise_adoption_report

            return enterprise_adoption_report(self.db)
        return {"error": f"unknown integration: {integration_id}"}


def _oidc_strict() -> bool:
    return os.environ.get("MERSAL_OIDC_STRICT", "1").strip().lower() not in {"0", "false"}


def _scheduler_jobs(autonomous: bool) -> list[str]:
    jobs = ["threat_feeds", "vuln_scan", "ai_train", "posture", "backup", "reliability"]
    if autonomous:
        jobs.extend(["siem_forward", "autonomous_cycle"])
    return jobs

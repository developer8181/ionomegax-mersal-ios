# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Unified integration status — world-class SOC fabric visibility."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Any

from ..db.adapter import uses_postgres
from ..config import postgres_dsn
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
        scim = ScimProvisioner(self.db)
        forwarders = self.db.list_siem_forwarders(enabled_only=True)
        cursor_raw = self.db.get_platform_setting("siem_forward_cursor", "{}")
        try:
            cursor = json.loads(cursor_raw)
        except json.JSONDecodeError:
            cursor = {}
        autonomous = os.environ.get("MERSAL_AUTONOMOUS", "1").strip().lower() not in {"0", "false"}
        return {
            "platform": "Mersal Global Integration Fabric",
            "tier": "enterprise-integrated",
            "identity": {
                "oidc": {"configured": oidc.configured(), "strict_jwt": _oidc_strict()},
                "saml": {"configured": saml.configured()},
                "scim": {
                    "token_env": bool(os.environ.get("MERSAL_SCIM_TOKEN", "").strip()),
                    "users": len(self.db.list_rbac_users()),
                },
                "ldap": bool(os.environ.get("MERSAL_LDAP_URL", "").strip()),
            },
            "data_plane": {
                "postgres_active": uses_postgres(),
                "postgres_configured": bool(postgres_dsn()),
                "siem_forwarders": len(forwarders),
                "siem_forward_cursor": cursor,
            },
            "operations": {
                "autonomous_enabled": autonomous,
                "scheduler_jobs": _scheduler_jobs(autonomous),
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


def _oidc_strict() -> bool:
    return os.environ.get("MERSAL_OIDC_STRICT", "1").strip().lower() not in {"0", "false"}


def _scheduler_jobs(autonomous: bool) -> list[str]:
    jobs = ["threat_feeds", "vuln_scan", "ai_train", "posture"]
    if autonomous:
        jobs.extend(["siem_forward", "autonomous_cycle"])
    return jobs

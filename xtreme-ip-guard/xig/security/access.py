# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Resolve principals and enforce route-level RBAC for bank/government deployments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..auth import (
    admin_password,
    auth_required,
    authorize,
    configured_token,
    decode_session,
    verify_admin,
)
from ..config import is_enterprise, is_production
from ..rbac.engine import PERMISSIONS, RbacEngine

if TYPE_CHECKING:
    from ..storage import Database


@dataclass(frozen=True)
class AccessContext:
    authenticated: bool
    principal: str
    role: str
    tenant_id: str
    auth_kind: str  # none | api_token | session | agent
    permissions: frozenset[str]

    def allows(self, permission: str) -> bool:
        if self.role == "super_admin":
            return True
        return permission in self.permissions


def resolve_access(
    database: "Database",
    *,
    token_header: str | None,
    tenant_header: str | None = None,
    actor_header: str | None = None,
) -> AccessContext:
    rbac = RbacEngine(database)
    default_tenant = (tenant_header or "default").strip() or "default"

    if not auth_required():
        perms = PERMISSIONS["super_admin"]
        return AccessContext(
            authenticated=True,
            principal=actor_header or "guest",
            role="super_admin",
            tenant_id=default_tenant,
            auth_kind="none",
            permissions=perms,
        )

    value = (token_header or "").strip()
    if value.startswith("Bearer "):
        value = value.removeprefix("Bearer ").strip()

    if not value:
        return AccessContext(
            authenticated=False,
            principal="",
            role="viewer",
            tenant_id=default_tenant,
            auth_kind="none",
            permissions=frozenset(),
        )

    api_token = configured_token()
    if api_token and value == api_token:
        role = "super_admin"
        return AccessContext(
            authenticated=True,
            principal=actor_header or "api-token",
            role=role,
            tenant_id=default_tenant,
            auth_kind="api_token",
            permissions=PERMISSIONS[role],
        )

    session = decode_session(value)
    if session:
        role = str(session.get("role", "analyst"))
        tenant = str(session.get("tenant_id", default_tenant))
        return AccessContext(
            authenticated=True,
            principal=str(session.get("username", "session")),
            role=role,
            tenant_id=tenant,
            auth_kind="session",
            permissions=PERMISSIONS.get(role, PERMISSIONS["viewer"]),
        )

    return AccessContext(
        authenticated=False,
        principal="",
        role="viewer",
        tenant_id=default_tenant,
        auth_kind="none",
        permissions=frozenset(),
    )


# method-sensitive prefix → permission
_ROUTE_RULES: list[tuple[str, str, str]] = [
    ("POST", "/api/policies", "policies.write"),
    ("POST", "/api/endpoints/", "endpoints.write"),
    ("POST", "/api/events", "events.read"),
    ("POST", "/api/agents/heartbeat", "endpoints.read"),
    ("POST", "/api/ai/train", "fabric.write"),
    ("POST", "/api/vuln/scan", "vuln.write"),
    ("POST", "/api/fabric/daily", "fabric.write"),
    ("POST", "/api/threat/sync", "threat.write"),
    ("POST", "/api/threat/taxii/sync", "threat.write"),
    ("POST", "/api/enterprise/cycle", "fabric.write"),
    ("POST", "/api/xdr/correlate", "xdr.write"),
    ("POST", "/api/logs/ingest", "siem.write"),
    ("POST", "/api/suricata/ingest", "siem.write"),
    ("POST", "/api/tenants", "tenants.write"),
    ("POST", "/api/users", "users.write"),
    ("POST", "/api/webhooks", "webhooks.write"),
    ("POST", "/api/incidents/", "incidents.write"),
    ("GET", "/api/policies", "policies.read"),
    ("GET", "/api/endpoints", "endpoints.read"),
    ("GET", "/api/events", "events.read"),
    ("GET", "/api/audit", "audit.read"),
    ("GET", "/api/siem/", "siem.read"),
    ("GET", "/api/incidents", "incidents.read"),
    ("GET", "/api/compliance", "compliance.read"),
    ("GET", "/api/xdr/", "xdr.read"),
    ("GET", "/api/edr/", "xdr.read"),
    ("GET", "/api/vuln/", "xdr.read"),
    ("GET", "/api/tenants", "tenants.read"),
    ("GET", "/api/users", "users.read"),
    ("GET", "/api/webhooks", "dashboard.read"),
    ("GET", "/api/reports/", "reports.export"),
    ("GET", "/api/global/", "dashboard.read"),
    ("GET", "/api/enterprise/", "dashboard.read"),
    ("GET", "/api/fabric/", "dashboard.read"),
    ("GET", "/api/ai/", "dashboard.read"),
    ("GET", "/api/dashboard", "dashboard.read"),
    ("GET", "/api/logs/", "siem.read"),
    ("GET", "/api/suricata/", "siem.read"),
    ("GET", "/api/yara/", "xdr.read"),
    ("GET", "/api/network/", "xdr.read"),
    ("GET", "/api/posture", "compliance.read"),
    ("GET", "/api/soar/", "incidents.read"),
    ("GET", "/api/agents", "endpoints.read"),
    ("GET", "/api/health", "dashboard.read"),
    ("GET", "/api/brand", "dashboard.read"),
    ("GET", "/api/threat/", "threat.write"),
    ("GET", "/api/alerts/stream", "siem.read"),
]


def permission_for_route(method: str, path: str) -> str:
    method = method.upper()
    for rule_method, prefix, perm in _ROUTE_RULES:
        if rule_method == method and (path == prefix or path.startswith(prefix)):
            return perm
    if method == "GET" and path.startswith("/api/"):
        return "dashboard.read"
    if method == "POST" and path.startswith("/api/"):
        return "fabric.write"
    return "dashboard.read"


def enterprise_startup_errors() -> list[str]:
    errors: list[str] = []
    if not is_enterprise():
        return errors
    if not is_production():
        errors.append("MERSAL_ENTERPRISE=1 requires MERSAL_PRODUCTION=1")
    return errors


def organization_startup_errors() -> list[str]:
    """Validation for any organization deployment (companies, NGOs, government)."""
    from ..auth import signing_secret_configured
    from ..config import is_dev_mode

    errors = list(enterprise_startup_errors())
    if is_dev_mode():
        return errors
    if not signing_secret_configured():
        errors.append("Set MERSAL_SIGNING_SECRET (32+ chars) or a strong MERSAL_API_TOKEN")
    if not (configured_token() or admin_password()):
        errors.append("Configure MERSAL_API_TOKEN and/or MERSAL_ADMIN_PASSWORD before exposing the API")
    return errors

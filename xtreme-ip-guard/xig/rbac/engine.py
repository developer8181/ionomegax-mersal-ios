# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""RBAC — roles and permissions aligned with enterprise SOC platforms."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database

ROLES = ("super_admin", "soc_admin", "analyst", "viewer")

PERMISSIONS: dict[str, frozenset[str]] = {
    "super_admin": frozenset(
        {
            "dashboard.read",
            "endpoints.read",
            "endpoints.write",
            "events.read",
            "policies.read",
            "policies.write",
            "audit.read",
            "siem.read",
            "siem.write",
            "incidents.read",
            "incidents.write",
            "compliance.read",
            "compliance.write",
            "xdr.read",
            "xdr.write",
            "fabric.write",
            "vuln.write",
            "threat.write",
            "tenants.read",
            "tenants.write",
            "users.read",
            "users.write",
            "webhooks.write",
            "reports.export",
            "admin.all",
        }
    ),
    "soc_admin": frozenset(
        {
            "dashboard.read",
            "endpoints.read",
            "endpoints.write",
            "events.read",
            "policies.read",
            "policies.write",
            "audit.read",
            "siem.read",
            "siem.write",
            "incidents.read",
            "incidents.write",
            "compliance.read",
            "xdr.read",
            "xdr.write",
            "fabric.write",
            "vuln.write",
            "threat.write",
            "reports.export",
        }
    ),
    "analyst": frozenset(
        {
            "dashboard.read",
            "endpoints.read",
            "events.read",
            "policies.read",
            "siem.read",
            "incidents.read",
            "incidents.write",
            "compliance.read",
            "xdr.read",
            "reports.export",
        }
    ),
    "viewer": frozenset(
        {
            "dashboard.read",
            "endpoints.read",
            "events.read",
            "siem.read",
            "incidents.read",
            "compliance.read",
            "xdr.read",
        }
    ),
}

ROUTE_PERMISSIONS: dict[str, str] = {
    "/api/policies": "policies.write",
    "/api/endpoints": "endpoints.read",
    "/api/audit": "audit.read",
    "/api/tenants": "tenants.read",
    "/api/users": "users.read",
    "/api/reports": "reports.export",
    "/api/webhooks": "webhooks.write",
    "/api/fabric/daily": "fabric.write",
    "/api/vuln/scan": "vuln.write",
    "/api/threat/sync": "threat.write",
    "/api/xdr/correlate": "xdr.write",
    "/api/enterprise/cycle": "fabric.write",
}


class RbacEngine:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def hash_password(self, password: str, *, salt: bytes | None = None) -> str:
        salt = salt or secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
        return f"pbkdf2${salt.hex()}${digest.hex()}"

    def verify_password(self, password: str, stored: str) -> bool:
        try:
            _, salt_hex, digest_hex = stored.split("$", 2)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
            return hmac.compare_digest(actual, expected)
        except (ValueError, OSError):
            return False

    def authenticate(self, username: str, password: str, *, tenant_id: str = "default") -> dict[str, Any] | None:
        user = self.db.get_rbac_user(username, tenant_id=tenant_id)
        if not user or not user.get("enabled"):
            return None
        if not self.verify_password(password, str(user.get("password_hash", ""))):
            return None
        return user

    def permissions_for_role(self, role: str) -> list[str]:
        return sorted(PERMISSIONS.get(role, PERMISSIONS["viewer"]))

    def role_has(self, role: str, permission: str) -> bool:
        if role == "super_admin":
            return True
        return permission in PERMISSIONS.get(role, frozenset())

    def check_route(self, role: str, path: str, *, method: str = "GET") -> bool:
        if role == "super_admin":
            return True
        if method == "GET" and not any(path.startswith(p) for p in ("/api/policies",)):
            if path.startswith("/api/") and path not in ROUTE_PERMISSIONS:
                return True
        for prefix, perm in ROUTE_PERMISSIONS.items():
            if path.startswith(prefix) or path == prefix:
                return self.role_has(role, perm)
        if method != "GET" and path.startswith("/api/"):
            return self.role_has(role, "fabric.write") or self.role_has(role, "incidents.write")
        return True

    def dashboard(self) -> dict[str, Any]:
        return {
            "module": "Mersal RBAC",
            "roles": list(ROLES),
            "users": self.db.list_rbac_users(),
        }

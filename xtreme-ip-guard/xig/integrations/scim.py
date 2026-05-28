# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""SCIM 2.0 provisioning — automated user lifecycle for enterprises."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class ScimProvisioner:
    SCIM_VERSION = "2.0"

    def __init__(self, database: "Database") -> None:
        self.db = database

    def verify_bearer(self, token: str) -> bool:
        import os

        expected = os.environ.get("MERSAL_SCIM_TOKEN", "").strip()
        if expected and hmac.compare_digest(token, expected):
            return True
        return self.db.verify_scim_token(token)

    def list_users(self, *, tenant_id: str = "default") -> dict[str, Any]:
        users = self.db.list_rbac_users(tenant_id=tenant_id)
        resources = [
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": u.get("user_id"),
                "userName": u.get("username"),
                "active": bool(u.get("enabled", 1)),
                "roles": [{"value": u.get("role")}],
            }
            for u in users
        ]
        return {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": len(resources),
            "Resources": resources,
        }

    def create_user(self, payload: dict[str, Any], *, tenant_id: str = "default") -> dict[str, Any]:
        from ..rbac import RbacEngine
        from ..security.password_policy import validate_password

        username = str(payload.get("userName", ""))
        password = secrets.token_urlsafe(24)
        role = "analyst"
        roles = payload.get("roles") or []
        if roles and isinstance(roles[0], dict):
            role = str(roles[0].get("value", role))
        rbac = RbacEngine(self.db)
        ok, msg = validate_password(password, username=username)
        if not ok:
            password = f"Mersal-{secrets.token_urlsafe(16)}!"
        user = self.db.create_rbac_user(
            username=username,
            password_hash=rbac.hash_password(password),
            role=role,
            tenant_id=tenant_id,
            display_name=str(payload.get("displayName", username)),
        )
        return {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": user.get("user_id"),
            "userName": username,
            "temporaryPassword": password,
        }

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

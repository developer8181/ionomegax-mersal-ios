# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""OpenID Connect — SSO for organizations (Azure AD, Keycloak, Okta compatible)."""

from __future__ import annotations

import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class OidcProvider:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def configured(self) -> bool:
        return bool(self._env_client() or self.db.list_oidc_clients(enabled_only=True))

    def authorization_url(self, *, state: str | None = None) -> dict[str, Any]:
        client = self._resolve_client()
        if not client:
            return {"error": "oidc not configured"}
        state = state or secrets.token_urlsafe(24)
        params = {
            "client_id": client["client_id"],
            "response_type": "code",
            "scope": client.get("scopes", "openid profile email"),
            "redirect_uri": client["redirect_uri"],
            "state": state,
        }
        base = client["issuer_url"].rstrip("/")
        url = f"{base}/authorize?{urllib.parse.urlencode(params)}"
        return {"authorization_url": url, "state": state}

    def exchange_code(self, code: str, *, state: str = "") -> dict[str, Any]:
        client = self._resolve_client()
        if not client:
            return {"error": "oidc not configured"}
        base = client["issuer_url"].rstrip("/")
        token_url = f"{base}/token"
        body = urllib.parse.urlencode(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": client["redirect_uri"],
                "client_id": client["client_id"],
                "client_secret": client.get("client_secret", ""),
            }
        ).encode()
        try:
            req = urllib.request.Request(
                token_url,
                data=body,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                tokens = json.loads(resp.read().decode())
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as exc:
            return {"error": str(exc)}
        id_token = tokens.get("id_token", "")
        username = self._username_from_id_token(id_token) or f"oidc-{secrets.token_hex(4)}"
        role = str(client.get("default_role", "analyst"))
        tenant_id = str(client.get("tenant_id", "default"))
        from ..auth import create_session_token

        session = create_session_token(username, role=role, tenant_id=tenant_id)
        return {
            "token": session,
            "username": username,
            "role": role,
            "tenant_id": tenant_id,
            "state": state,
        }

    def _resolve_client(self) -> dict[str, Any] | None:
        env = self._env_client()
        if env:
            return env
        clients = self.db.list_oidc_clients(enabled_only=True)
        return clients[0] if clients else None

    def _env_client(self) -> dict[str, Any] | None:
        issuer = os.environ.get("MERSAL_OIDC_ISSUER", "").strip()
        client_id = os.environ.get("MERSAL_OIDC_CLIENT_ID", "").strip()
        if not issuer or not client_id:
            return None
        return {
            "issuer_url": issuer,
            "client_id": client_id,
            "client_secret": os.environ.get("MERSAL_OIDC_CLIENT_SECRET", "").strip(),
            "redirect_uri": os.environ.get(
                "MERSAL_OIDC_REDIRECT_URI", "http://127.0.0.1:8090/api/auth/oidc/callback"
            ).strip(),
            "scopes": os.environ.get("MERSAL_OIDC_SCOPES", "openid profile email"),
            "default_role": os.environ.get("MERSAL_OIDC_DEFAULT_ROLE", "analyst"),
            "tenant_id": os.environ.get("MERSAL_OIDC_TENANT_ID", "default"),
        }

    @staticmethod
    def _username_from_id_token(id_token: str) -> str:
        if not id_token or "." not in id_token:
            return ""
        try:
            import base64

            payload = id_token.split(".")[1]
            padded = payload + "=" * (-len(payload) % 4)
            data = json.loads(base64.urlsafe_b64decode(padded.encode()))
            return str(data.get("preferred_username") or data.get("email") or data.get("sub") or "")
        except (ValueError, json.JSONDecodeError, OSError):
            return ""

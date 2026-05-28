# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""SAML 2.0 SP — enterprise SSO (Okta, Azure AD SAML, ADFS)."""

from __future__ import annotations

import base64
import os
import secrets
import urllib.parse
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class SamlProvider:
    NS = {"saml": "urn:oasis:names:tc:SAML:2.0:assertion", "samlp": "urn:oasis:names:tc:SAML:2.0:protocol"}

    def __init__(self, database: "Database") -> None:
        self.db = database

    def configured(self) -> bool:
        return bool(self._env_config() or self.db.list_saml_providers(enabled_only=True))

    def login_redirect(self) -> dict[str, Any]:
        cfg = self._env_config() or (self.db.list_saml_providers(enabled_only=True) or [None])[0]
        if not cfg:
            return {"error": "saml not configured"}
        state = secrets.token_urlsafe(16)
        params = {
            "SAMLRequest": base64.b64encode(b"PLACEHOLDER_REQUEST").decode(),
            "RelayState": state,
        }
        url = f"{cfg['sso_url']}?{urllib.parse.urlencode(params)}"
        return {"redirect_url": url, "state": state, "note": "Configure IdP metadata; use POST ACS for production"}

    def consume_response(self, saml_response_b64: str) -> dict[str, Any]:
        try:
            xml_bytes = base64.b64decode(saml_response_b64)
            root = ET.fromstring(xml_bytes)
        except (ET.ParseError, ValueError, OSError) as exc:
            return {"error": f"invalid SAML response: {exc}"}
        name_id = ""
        for elem in root.iter():
            if elem.tag.endswith("NameID") and elem.text:
                name_id = elem.text.strip()
                break
        if not name_id:
            return {"error": "NameID not found in assertion"}
        cfg = self._env_config() or {}
        role = str(cfg.get("default_role", "analyst"))
        tenant_id = str(cfg.get("tenant_id", "default"))
        from ..auth import create_session_token

        return {
            "token": create_session_token(name_id, role=role, tenant_id=tenant_id),
            "username": name_id,
            "role": role,
            "tenant_id": tenant_id,
            "auth": "saml",
        }

    def _env_config(self) -> dict[str, Any] | None:
        sso = os.environ.get("MERSAL_SAML_SSO_URL", "").strip()
        if not sso:
            return None
        return {
            "sso_url": sso,
            "entity_id": os.environ.get("MERSAL_SAML_ENTITY_ID", "mersal-sp"),
            "default_role": os.environ.get("MERSAL_SAML_DEFAULT_ROLE", "analyst"),
            "tenant_id": os.environ.get("MERSAL_SAML_TENANT_ID", "default"),
        }

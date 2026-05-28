# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""SAML 2.0 SP — enterprise SSO (Okta, Azure AD SAML, ADFS)."""

from __future__ import annotations

import base64
import os
import secrets
import urllib.parse
import zlib
from datetime import datetime, timezone
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
        request_xml = self._build_authn_request(cfg)
        deflated = zlib.compressobj(wbits=-15)
        payload = deflated.compress(request_xml.encode("utf-8")) + deflated.flush()
        encoded_request = base64.b64encode(payload).decode()
        params = {
            "SAMLRequest": encoded_request,
            "RelayState": state,
        }
        url = f"{cfg['sso_url']}?{urllib.parse.urlencode(params)}"
        return {"redirect_url": url, "state": state, "binding": "HTTP-Redirect"}

    def _build_authn_request(self, cfg: dict[str, Any]) -> str:
        issue_instant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        request_id = f"_{secrets.token_hex(12)}"
        entity_id = str(cfg.get("entity_id", "mersal-sp"))
        acs = os.environ.get("MERSAL_SAML_ACS_URL", "http://127.0.0.1:8090/api/auth/saml/acs").strip()
        return (
            f'<samlp:AuthnRequest xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol" '
            f'xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" '
            f'ID="{request_id}" Version="2.0" IssueInstant="{issue_instant}" '
            f'Destination="{cfg["sso_url"]}" AssertionConsumerServiceURL="{acs}" '
            f'ProtocolBinding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST">'
            f'<saml:Issuer>{entity_id}</saml:Issuer>'
            f'<samlp:NameIDPolicy Format="urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress" '
            f'AllowCreate="true"/></samlp:AuthnRequest>'
        )

    def consume_response(self, saml_response_b64: str) -> dict[str, Any]:
        try:
            xml_bytes = base64.b64decode(saml_response_b64)
        except (ValueError, OSError) as exc:
            return {"error": f"invalid SAML response: {exc}"}
        cfg = self._env_config() or {}
        from .saml_verify import verify_saml_response

        ok, err, claims = verify_saml_response(
            xml_bytes,
            sp_entity_id=str(cfg.get("entity_id", os.environ.get("MERSAL_SAML_ENTITY_ID", "mersal-sp"))),
            idp_cert_pem=os.environ.get("MERSAL_SAML_IDP_CERT", ""),
        )
        if not ok:
            return {"error": err}
        name_id = str(claims.get("name_id", ""))
        if not name_id:
            return {"error": "NameID not found in assertion"}
        from .federation_roles import resolve_role_from_claims

        role = resolve_role_from_claims(claims, default_role=str(cfg.get("default_role", "analyst")))
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

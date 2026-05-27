"""Production deployment validation and checklist."""

from __future__ import annotations

import secrets
from typing import Any

from .config import Settings

INSECURE_SECRETS = frozenset(
    {
        "change-me-in-production",
        "changeme",
        "secret",
        "replace-with-long-random-secret",
        "replace-with-agent-token",
    }
)


def validate_production_settings(settings: Settings) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for production mode."""
    errors: list[str] = []
    warnings: list[str] = []

    if not settings.production_mode:
        warnings.append("EPMS_PRODUCTION is not enabled; using development defaults")
        return errors, warnings

    if settings.session_secret.lower() in INSECURE_SECRETS or len(settings.session_secret) < 32:
        errors.append("EPMS_SESSION_SECRET must be at least 32 random characters in production")
    if not settings.require_auth:
        errors.append("EPMS_REQUIRE_AUTH must be true in production")
    if not settings.agent_token or settings.agent_token.lower() in INSECURE_SECRETS:
        errors.append("EPMS_AGENT_TOKEN must be set to a strong random value in production")
    if not settings.bootstrap_admin_password:
        warnings.append("Set EPMS_BOOTSTRAP_ADMIN_PASSWORD on first install, then remove it")
    if settings.host == "127.0.0.1":
        warnings.append("EPMS_HOST is loopback; set 0.0.0.0 for server deployment")
    if settings.tls_cert is None:
        warnings.append("TLS is not configured; use reverse proxy or EPMS_TLS_CERT/KEY")

    return errors, warnings


def production_checklist(database_ok: bool, settings: Settings) -> dict[str, Any]:
    errors, warnings = validate_production_settings(settings)
    return {
        "production_mode": settings.production_mode,
        "ready": database_ok and not errors,
        "errors": errors,
        "warnings": warnings,
        "items": [
            {"id": "database", "ok": database_ok},
            {"id": "auth", "ok": settings.require_auth},
            {"id": "agent_token", "ok": bool(settings.agent_token)},
            {"id": "session_secret", "ok": settings.session_secret.lower() not in INSECURE_SECRETS},
            {"id": "anonymize_docs", "ok": settings.anonymize_documents},
            {"id": "device_servlet", "ok": True},
            {"id": "sdk_clients", "ok": True},
        ],
    }


def generate_secret(length: int = 48) -> str:
    return secrets.token_urlsafe(length)

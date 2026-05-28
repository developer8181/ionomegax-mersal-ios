# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Runtime configuration — production vs development."""

from __future__ import annotations

import os
from pathlib import Path


def is_production() -> bool:
    return os.environ.get("MERSAL_PRODUCTION", "").strip().lower() in {"1", "true", "yes", "on"}


def should_bootstrap_on_start() -> bool:
    if os.environ.get("MERSAL_BOOTSTRAP", "").strip().lower() in {"1", "true", "yes"}:
        return True
    if not is_production():
        return True
    return False


def data_directory() -> Path:
    db = os.environ.get("MERSAL_DB", os.environ.get("XIG_DB", ""))
    if db:
        return Path(db).parent
    return Path(__file__).resolve().parents[1] / "data"


def tls_enabled() -> bool:
    cert = os.environ.get("MERSAL_TLS_CERT", "").strip()
    key = os.environ.get("MERSAL_TLS_KEY", "").strip()
    return bool(cert and key and Path(cert).is_file() and Path(key).is_file())


def allow_demo_seed() -> bool:
    """Demo endpoint/policies only when explicitly allowed in production."""
    if os.environ.get("MERSAL_DEMO_UI", "").strip().lower() in {"1", "true", "yes"}:
        return True
    return not is_production()


def agent_mtls_required() -> bool:
    return os.environ.get("MERSAL_AGENT_MTLS", "").strip().lower() in {"1", "true", "yes"}


def agent_ca_path() -> Path | None:
    path = os.environ.get("MERSAL_AGENT_CA", "").strip()
    if path and Path(path).is_file():
        return Path(path)
    return None


def is_enterprise() -> bool:
    """Bank / government hardened profile (requires production + secrets)."""
    return os.environ.get("MERSAL_ENTERPRISE", "").strip().lower() in {"1", "true", "yes", "on"}


def enterprise_strict() -> bool:
    """Mandatory TLS, Postgres, dedicated update signing — set MERSAL_ENTERPRISE_STRICT=1."""
    return os.environ.get("MERSAL_ENTERPRISE_STRICT", "").strip().lower() in {"1", "true", "yes", "on"}


def ldap_enabled() -> bool:
    return bool(os.environ.get("MERSAL_LDAP_URL", "").strip())


def encryption_at_rest_enabled() -> bool:
    return os.environ.get("MERSAL_DB_ENCRYPTION", "").strip().lower() in {"1", "true", "yes"}


def postgres_dsn() -> str:
    return os.environ.get("MERSAL_POSTGRES_DSN", "").strip()


def is_dev_mode() -> bool:
    """Local lab only — disables mandatory auth when no secrets configured."""
    return os.environ.get("MERSAL_DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}


def require_agent_keys() -> bool:
    """Each endpoint agent must use its own API key (recommended for all organizations)."""
    if is_dev_mode():
        return False
    if is_enterprise() or is_production():
        return os.environ.get("MERSAL_REQUIRE_AGENT_KEYS", "1").strip().lower() not in {
            "0",
            "false",
            "no",
        }
    return os.environ.get("MERSAL_REQUIRE_AGENT_KEYS", "").strip().lower() in {"1", "true", "yes"}

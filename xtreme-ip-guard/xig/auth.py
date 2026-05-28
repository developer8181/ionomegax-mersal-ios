# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Authentication for Mersal Guard API and Command Center."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from typing import Any

from .config import is_dev_mode, is_enterprise, is_production


def configured_token() -> str:
    return os.environ.get("MERSAL_API_TOKEN", os.environ.get("XIG_API_TOKEN", "")).strip()


def admin_username() -> str:
    return os.environ.get("MERSAL_ADMIN_USER", "admin").strip() or "admin"


def admin_password() -> str:
    return os.environ.get("MERSAL_ADMIN_PASSWORD", "").strip()


def signing_secret_configured() -> bool:
    secret = os.environ.get("MERSAL_SIGNING_SECRET", "").strip()
    if len(secret) >= 32:
        return True
    return bool(configured_token() and len(configured_token()) >= 24)


def auth_required() -> bool:
    """Professional default: API is never open on the public internet unless DEV_MODE."""
    if is_dev_mode():
        return bool(configured_token() or admin_password())
    return True


def verify_admin(username: str, password: str) -> bool:
    expected_user = admin_username()
    expected_pass = admin_password()
    if not expected_pass:
        return False
    return secrets.compare_digest(username.strip(), expected_user) and secrets.compare_digest(
        password, expected_pass
    )


def _signing_secret() -> str:
    explicit = os.environ.get("MERSAL_SIGNING_SECRET", "").strip()
    if explicit:
        return explicit
    token = configured_token()
    if token:
        return token
    pwd = admin_password()
    if pwd:
        return hashlib.sha256(pwd.encode()).hexdigest()
    if is_enterprise() or is_production() or not is_dev_mode():
        raise RuntimeError("MERSAL_SIGNING_SECRET or MERSAL_API_TOKEN required — set MERSAL_DEV_MODE=1 for local lab only")
    return "mersal-dev-insecure-only-for-local-lab"


def create_session_token(
    username: str,
    *,
    role: str = "analyst",
    tenant_id: str = "default",
    ttl_seconds: int = 86_400,
) -> str:
    issued_at = int(time.time())
    payload = f"{username}|{role}|{tenant_id}|{issued_at}|{ttl_seconds}"
    signature = hmac.new(_signing_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}|{signature}".encode()
    return base64.urlsafe_b64encode(raw).decode()


def decode_session(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        body = raw.decode()
        if "|" in body:
            username, role, tenant_id, issued_at, ttl_seconds, signature = body.rsplit("|", 5)
            payload = f"{username}|{role}|{tenant_id}|{issued_at}|{ttl_seconds}"
        else:
            username, issued_at, ttl_seconds, signature = body.rsplit(":", 3)
            role, tenant_id = "admin", "default"
            payload = f"{username}:{issued_at}:{ttl_seconds}"
        expected = hmac.new(_signing_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not secrets.compare_digest(signature, expected):
            return None
        age = int(time.time()) - int(issued_at)
        if age > int(ttl_seconds):
            return None
        return {
            "username": username,
            "role": role,
            "tenant_id": tenant_id,
            "issued_at": issued_at,
            "ttl_seconds": ttl_seconds,
        }
    except (ValueError, OSError, RuntimeError):
        return None


def verify_session_token(token: str | None) -> bool:
    return decode_session(token) is not None


def authorize(header_value: str | None) -> bool:
    if not auth_required():
        return True
    if not header_value:
        return False
    value = header_value.strip()
    if value.startswith("Bearer "):
        value = value.removeprefix("Bearer ").strip()
    api_token = configured_token()
    if api_token and secrets.compare_digest(value, api_token):
        return True
    if verify_session_token(value):
        return True
    return False

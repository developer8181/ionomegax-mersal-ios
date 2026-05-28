# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Authentication for Mersal Guard API and Command Center."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time


def configured_token() -> str:
    return os.environ.get("MERSAL_API_TOKEN", os.environ.get("XIG_API_TOKEN", "")).strip()


def admin_username() -> str:
    return os.environ.get("MERSAL_ADMIN_USER", "admin").strip() or "admin"


def admin_password() -> str:
    return os.environ.get("MERSAL_ADMIN_PASSWORD", "").strip()


def auth_required() -> bool:
    return bool(configured_token() or admin_password())


def verify_admin(username: str, password: str) -> bool:
    expected_user = admin_username()
    expected_pass = admin_password()
    if not expected_pass:
        return False
    return secrets.compare_digest(username.strip(), expected_user) and secrets.compare_digest(
        password, expected_pass
    )


def _signing_secret() -> str:
    return configured_token() or admin_password() or "mersal-dev-insecure"


def create_session_token(username: str, *, ttl_seconds: int = 86_400) -> str:
    issued_at = int(time.time())
    payload = f"{username}:{issued_at}:{ttl_seconds}"
    signature = hmac.new(_signing_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
    raw = f"{payload}:{signature}".encode()
    return base64.urlsafe_b64encode(raw).decode()


def _decode_session_token(token: str | None) -> dict[str, str] | None:
    if not token:
        return None
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        username, issued_at, ttl_seconds, signature = raw.decode().rsplit(":", 3)
        payload = f"{username}:{issued_at}:{ttl_seconds}"
        expected = hmac.new(_signing_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not secrets.compare_digest(signature, expected):
            return None
        age = int(time.time()) - int(issued_at)
        if age > int(ttl_seconds):
            return None
        return {"username": username, "issued_at": issued_at, "ttl_seconds": ttl_seconds}
    except (ValueError, OSError):
        return None


def verify_session_token(token: str | None) -> bool:
    return _decode_session_token(token) is not None


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

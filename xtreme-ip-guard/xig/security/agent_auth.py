# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Per-agent API credentials — organizations issue unique keys per endpoint."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import TYPE_CHECKING

from ..auth import configured_token
from ..config import require_agent_keys

if TYPE_CHECKING:
    from ..storage import Database


def generate_agent_key() -> str:
    return f"mag_{secrets.token_urlsafe(32)}"


def hash_agent_key(key: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, 200_000)
    return f"pbkdf2${salt.hex()}${digest.hex()}"


def verify_agent_key(key: str, stored: str) -> bool:
    try:
        _, salt_hex, digest_hex = stored.split("$", 2)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, 200_000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, OSError):
        return False


def authorize_agent_request(
    database: "Database",
    *,
    agent_id: str,
    agent_key_header: str | None,
    bearer_token: str | None,
) -> bool:
    global_token = configured_token()
    if global_token and bearer_token and secrets.compare_digest(bearer_token, global_token):
        return True
    if not require_agent_keys() and not agent_key_header:
        return bool(global_token and bearer_token and secrets.compare_digest(bearer_token, global_token))

    key = (agent_key_header or bearer_token or "").strip()
    if not key or not agent_id:
        return False
    stored = database.get_agent_key_hash(agent_id)
    if stored and verify_agent_key(key, stored):
        return True
    if global_token and secrets.compare_digest(key, global_token):
        return True
    return False

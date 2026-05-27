"""Admin authentication, sessions, and role-based access control."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

SESSION_HEADER = "X-EPMS-Session"
SESSION_COOKIE = "epms_session"
SESSION_TTL_HOURS = 12

ROLES = ("superadmin", "admin", "operator", "viewer")

PERMISSIONS: dict[str, frozenset[str]] = {
    "superadmin": frozenset(
        {
            "view",
            "manage_jobs",
            "manage_users",
            "manage_printers",
            "manage_pricing",
            "manage_settings",
            "manage_agents",
            "demo_reset",
        }
    ),
    "admin": frozenset(
        {
            "view",
            "manage_jobs",
            "manage_users",
            "manage_printers",
            "manage_pricing",
            "manage_agents",
            "demo_reset",
        }
    ),
    "operator": frozenset({"view", "manage_jobs"}),
    "viewer": frozenset({"view"}),
}


@dataclass(frozen=True)
class AdminUser:
    id: int
    username: str
    role: str
    display_name: str

    def has_permission(self, permission: str) -> bool:
        return permission in PERMISSIONS.get(self.role, frozenset())


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if not password:
        raise ValueError("password is required")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"pbkdf2_sha256${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = encoded.split("$", 2)
        if scheme != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except (TypeError, ValueError):
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def session_expiry_iso(*, hours: int = SESSION_TTL_HOURS) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=hours)
    return expires.replace(microsecond=0).isoformat()


def is_session_active(expires_at: str) -> bool:
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry > datetime.now(timezone.utc)
    except ValueError:
        return False


def user_to_dict(user: AdminUser) -> dict[str, Any]:
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "display_name": user.display_name,
        "permissions": sorted(PERMISSIONS.get(user.role, frozenset())),
    }

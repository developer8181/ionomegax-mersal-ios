"""Policy bundle integrity and agent authentication primitives."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any


def generate_api_key(prefix: str = "eipg") -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def hash_chain(previous_hash: str, payload: str) -> str:
    """Append-only audit chain — each entry links to the previous hash."""
    material = f"{previous_hash}|{payload}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def sign_policy_bundle(payload: dict[str, Any], secret: str) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_policy_bundle(payload: dict[str, Any], signature: str, secret: str) -> bool:
    expected = sign_policy_bundle(payload, secret)
    return hmac.compare_digest(expected, signature)


def policy_bundle_hash(rules: list[dict[str, Any]], version: int) -> str:
    material = json.dumps({"version": version, "rules": rules}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]

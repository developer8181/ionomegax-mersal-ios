"""Cryptographic helpers for Extreme IP Guard.

This module is intentionally crypto-agile: every signed or wrapped artefact
includes an ``alg`` identifier so the algorithm can be rotated without
breaking older signatures. We rely only on :mod:`hmac`, :mod:`hashlib`, and
:mod:`secrets` from the standard library to keep the reference
implementation portable.

For production deployments, the :class:`AgentKeyPair` and :func:`sign_blob`
primitives should be backed by Ed25519 (or hybrid PQC) from a vetted
library; the surface area defined here is designed so swapping is a one
file change.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Any

from .core import canonical_json


HMAC_ALG = "HMAC-SHA256"
ENROLMENT_TOKEN_BYTES = 24
SESSION_KEY_BYTES = 32


def b64encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def random_token(length: int = ENROLMENT_TOKEN_BYTES) -> str:
    """Generate a URL-safe one-time token (used for enrolment)."""

    return secrets.token_urlsafe(length)


def hash_password(password: str, *, salt: bytes | None = None, iterations: int = 240_000) -> dict[str, str]:
    """Hash a console password with PBKDF2-HMAC-SHA256.

    Returns a dict carrying the algorithm identifier so the hash format is
    self-describing and rotation-friendly.
    """

    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return {
        "alg": "PBKDF2-SHA256",
        "iter": str(iterations),
        "salt": b64encode(salt),
        "hash": b64encode(digest),
    }


def verify_password(password: str, stored: dict[str, str]) -> bool:
    if stored.get("alg") != "PBKDF2-SHA256":
        return False
    salt = b64decode(stored["salt"])
    iterations = int(stored.get("iter", "240000"))
    expected = b64decode(stored["hash"])
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(expected, digest)


@dataclass(frozen=True)
class AgentKeyPair:
    """A lightweight HMAC-based agent identity for the reference build.

    The ``public_key`` here is not a real asymmetric public key; it is a
    server-known shared key fingerprint. Production agents must replace this
    with Ed25519 and keep the private key in OS-level secure storage
    (Windows DPAPI, macOS Keychain, Linux kernel keyring).
    """

    agent_id: str
    secret: str
    public_key: str

    @classmethod
    def generate(cls, agent_id: str) -> "AgentKeyPair":
        secret = secrets.token_bytes(SESSION_KEY_BYTES)
        public = hashlib.sha256(secret).digest()
        return cls(
            agent_id=agent_id,
            secret=b64encode(secret),
            public_key=b64encode(public),
        )


def sign_blob(secret_b64: str, payload: Any) -> str:
    """Sign a JSON-serializable payload with HMAC-SHA256.

    The signature covers the canonical JSON representation, which is the
    same encoding used everywhere else (storage, audit chain, network).
    """

    secret = b64decode(secret_b64)
    mac = hmac.new(secret, canonical_json(payload).encode("utf-8"), hashlib.sha256)
    return f"{HMAC_ALG}:{b64encode(mac.digest())}"


def verify_blob(secret_b64: str, payload: Any, signature: str) -> bool:
    if not signature or ":" not in signature:
        return False
    alg, mac_b64 = signature.split(":", 1)
    if alg != HMAC_ALG:
        return False
    try:
        expected = b64decode(mac_b64)
    except (ValueError, base64.binascii.Error):
        return False
    secret = b64decode(secret_b64)
    mac = hmac.new(secret, canonical_json(payload).encode("utf-8"), hashlib.sha256).digest()
    return hmac.compare_digest(expected, mac)


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def chain_hash(prev_hash: str, record: dict[str, Any]) -> str:
    """Compute ``SHA256(prev_hash || canonical_json(record))``.

    Used by both the event ledger and the admin audit chain so any
    after-the-fact modification can be detected by replaying the chain.
    """

    body = canonical_json(record)
    digest = hashlib.sha256()
    digest.update(prev_hash.encode("utf-8"))
    digest.update(b"\n")
    digest.update(body.encode("utf-8"))
    return digest.hexdigest()


def merkle_root(hashes: list[str]) -> str:
    """Compute a Merkle root for a list of hex hashes.

    Used to checkpoint shards of the event ledger. Empty input returns the
    sha256 of an empty string for a deterministic "empty root" value.
    """

    if not hashes:
        return sha256_hex(b"")
    layer = [bytes.fromhex(h) for h in hashes]
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        layer = [hashlib.sha256(layer[i] + layer[i + 1]).digest() for i in range(0, len(layer), 2)]
    return layer[0].hex()

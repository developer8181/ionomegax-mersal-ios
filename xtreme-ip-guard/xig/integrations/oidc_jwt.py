# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""OIDC id_token verification via issuer JWKS (RS256)."""

from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from typing import Any

_JWKS_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 3600


def verify_id_token(id_token: str, *, issuer: str, client_id: str) -> tuple[bool, dict[str, Any], str]:
    if not id_token or id_token.count(".") != 2:
        return False, {}, "malformed token"
    try:
        header_b64, payload_b64, sig_b64 = id_token.split(".")
        header = _json_segment(header_b64)
        payload = _json_segment(payload_b64)
    except (ValueError, json.JSONDecodeError) as exc:
        return False, {}, str(exc)

    alg = str(header.get("alg", ""))
    if alg not in {"RS256", "PS256"}:
        return False, payload, f"unsupported alg: {alg}"

    kid = str(header.get("kid", ""))
    jwks = _fetch_jwks(issuer)
    key = _select_jwk(jwks, kid)
    if not key:
        return False, payload, "no matching JWK"

    if not _verify_signature(id_token, key, alg):
        return False, payload, "signature verification failed"

    now = int(time.time())
    iss = str(payload.get("iss", "")).rstrip("/")
    if iss and iss != issuer.rstrip("/"):
        return False, payload, "issuer mismatch"
    aud = payload.get("aud")
    if isinstance(aud, list):
        if client_id not in aud:
            return False, payload, "audience mismatch"
    elif aud and str(aud) != client_id:
        return False, payload, "audience mismatch"
    exp = int(payload.get("exp", 0) or 0)
    if exp and now > exp + 60:
        return False, payload, "token expired"
    nbf = int(payload.get("nbf", 0) or 0)
    if nbf and now + 60 < nbf:
        return False, payload, "token not yet valid"

    return True, payload, ""


def _json_segment(segment: str) -> dict[str, Any]:
    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode()))


def _fetch_jwks(issuer: str) -> dict[str, Any]:
    base = issuer.rstrip("/")
    cached = _JWKS_CACHE.get(base)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        return cached[1]
    discovery_url = f"{base}/.well-known/openid-configuration"
    try:
        with urllib.request.urlopen(discovery_url, timeout=12) as resp:
            meta = json.loads(resp.read().decode())
        jwks_uri = str(meta.get("jwks_uri", f"{base}/protocol/openid-connect/certs"))
        with urllib.request.urlopen(jwks_uri, timeout=12) as resp:
            jwks = json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError):
        jwks = {"keys": []}
    _JWKS_CACHE[base] = (time.time(), jwks)
    return jwks


def _select_jwk(jwks: dict[str, Any], kid: str) -> dict[str, Any] | None:
    keys = jwks.get("keys") or []
    for key in keys:
        if kid and str(key.get("kid", "")) == kid:
            return key
    return keys[0] if keys else None


def _verify_signature(token: str, jwk: dict[str, Any], alg: str) -> bool:
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding, rsa
    except ImportError:
        return False

    header_b64, payload_b64, sig_b64 = token.split(".")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))

    n = _b64int(jwk["n"])
    e = _b64int(jwk["e"])
    public_key = rsa.RSAPublicNumbers(e, n).public_key()

    if alg == "RS256":
        public_key.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
        return True
    if alg == "PS256":
        public_key.verify(
            signature,
            signing_input,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256(),
        )
        return True
    return False


def _b64int(value: str) -> int:
    raw = base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    return int.from_bytes(raw, "big")

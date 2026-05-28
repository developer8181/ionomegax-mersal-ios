# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""HTTP hardening — rate limits, security headers, body limits (SOC-grade defaults)."""

from __future__ import annotations

import ipaddress
import os
import time
from collections import defaultdict
from threading import Lock
from typing import Callable

from ..config import tls_enabled

_MAX_BODY_BYTES = int(os.environ.get("MERSAL_MAX_BODY_BYTES", "1048576"))  # 1 MiB
_RATE_LIMIT_PER_MIN = int(os.environ.get("MERSAL_RATE_LIMIT_PER_MIN", "300"))
_LOGIN_RATE_LIMIT = int(os.environ.get("MERSAL_LOGIN_RATE_LIMIT_PER_MIN", "10"))


class RateLimiter:
    """Thread-safe sliding window per client IP."""

    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max(1, max_per_minute)
        self._events: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        window_start = now - 60.0
        with self._lock:
            bucket = self._events[key]
            self._events[key] = [t for t in bucket if t >= window_start]
            if len(self._events[key]) >= self.max_per_minute:
                return False
            self._events[key].append(now)
            return True


_api_limiter = RateLimiter(_RATE_LIMIT_PER_MIN)
_login_limiter = RateLimiter(_LOGIN_RATE_LIMIT)


def client_ip(headers: dict[str, str], client_address: tuple[str, int] | None) -> str:
    forwarded = headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if client_address:
        return client_address[0]
    return "unknown"


def check_rate_limit(*, path: str, client_key: str) -> bool:
    if path == "/api/auth/login":
        return _login_limiter.allow(client_key)
    if path.startswith("/api/"):
        return _api_limiter.allow(client_key)
    return True


def max_body_bytes() -> int:
    return _MAX_BODY_BYTES


def admin_ip_allowed(client_ip_str: str) -> bool:
    raw = os.environ.get("MERSAL_ADMIN_IP_ALLOWLIST", "").strip()
    if not raw:
        return True
    try:
        addr = ipaddress.ip_address(client_ip_str)
    except ValueError:
        return False
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "/" in part:
            if addr in ipaddress.ip_network(part, strict=False):
                return True
        elif addr == ipaddress.ip_address(part):
            return True
    return False


def apply_security_headers(send_header: Callable[[str, str], None], *, path: str = "") -> None:
    send_header("X-Content-Type-Options", "nosniff")
    send_header("X-Frame-Options", "DENY")
    send_header("Referrer-Policy", "strict-origin-when-cross-origin")
    send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    send_header("Cache-Control", "no-store")
    if tls_enabled():
        send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if path.startswith("/console"):
        send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
        )

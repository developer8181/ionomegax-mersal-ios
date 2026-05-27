"""
Extreme IP Guard - Adaptive Rate Limiter
Token-bucket rate limiter with sliding window counters and
dynamic threshold adjustment based on threat scores.
"""

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

from config.settings import settings


@dataclass
class TokenBucket:
    capacity: float
    tokens: float
    refill_rate: float
    last_refill: float = field(default_factory=time.monotonic)

    def consume(self, tokens: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


@dataclass
class SlidingWindowCounter:
    window_size: int
    max_requests: int
    timestamps: list = field(default_factory=list)

    def record_and_check(self) -> Tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - self.window_size
        self.timestamps = [t for t in self.timestamps if t > cutoff]
        self.timestamps.append(now)
        count = len(self.timestamps)
        return count <= self.max_requests, count


class AdaptiveRateLimiter:
    """
    Rate limiter that adapts limits per-IP based on threat score.
    Higher-threat IPs get progressively tighter limits.
    """

    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._windows: Dict[str, SlidingWindowCounter] = {}
        self._threat_scores: Dict[str, float] = {}
        self._blocked_until: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _get_adjusted_limits(self, ip: str) -> Tuple[int, float]:
        threat_score = self._threat_scores.get(ip, 0.0)
        base_max = settings.RATE_LIMIT_MAX_REQUESTS
        base_window = settings.RATE_LIMIT_WINDOW_SECONDS

        if threat_score >= 80:
            return max(5, int(base_max * 0.05)), base_window
        elif threat_score >= 60:
            return max(10, int(base_max * 0.15)), base_window
        elif threat_score >= 40:
            return max(20, int(base_max * 0.3)), base_window
        elif threat_score >= 20:
            return int(base_max * 0.6), base_window
        return base_max, base_window

    async def check_rate_limit(self, ip: str) -> dict:
        async with self._lock:
            blocked_until = self._blocked_until.get(ip, 0)
            if time.monotonic() < blocked_until:
                return {
                    "allowed": False,
                    "ip": ip,
                    "reason": "temporarily_blocked",
                    "retry_after": int(blocked_until - time.monotonic()),
                    "current_count": -1,
                    "max_allowed": 0,
                }

            max_requests, window = self._get_adjusted_limits(ip)

            if ip not in self._windows:
                self._windows[ip] = SlidingWindowCounter(
                    window_size=window, max_requests=max_requests
                )
            else:
                self._windows[ip].max_requests = max_requests

            allowed, count = self._windows[ip].record_and_check()

            if not allowed:
                penalty_seconds = min(300, 30 * (count / max_requests))
                self._blocked_until[ip] = time.monotonic() + penalty_seconds

            if ip not in self._buckets:
                refill_rate = max_requests / window
                self._buckets[ip] = TokenBucket(
                    capacity=max_requests,
                    tokens=max_requests,
                    refill_rate=refill_rate,
                )

            bucket_ok = self._buckets[ip].consume()

            final_allowed = allowed and bucket_ok

            return {
                "allowed": final_allowed,
                "ip": ip,
                "reason": "ok" if final_allowed else "rate_limit_exceeded",
                "current_count": count,
                "max_allowed": max_requests,
                "remaining": max(0, max_requests - count),
                "window_seconds": window,
            }

    def update_threat_score(self, ip: str, score: float):
        self._threat_scores[ip] = score

    async def cleanup_expired(self):
        async with self._lock:
            now = time.monotonic()
            expired_blocks = [
                ip for ip, until in self._blocked_until.items() if now >= until
            ]
            for ip in expired_blocks:
                del self._blocked_until[ip]

            stale_windows = [
                ip for ip, w in self._windows.items()
                if w.timestamps and (now - w.timestamps[-1]) > w.window_size * 3
            ]
            for ip in stale_windows:
                del self._windows[ip]
                self._buckets.pop(ip, None)

    def get_stats(self) -> dict:
        return {
            "active_buckets": len(self._buckets),
            "active_windows": len(self._windows),
            "blocked_ips": len(self._blocked_until),
            "tracked_threat_scores": len(self._threat_scores),
        }


rate_limiter = AdaptiveRateLimiter()

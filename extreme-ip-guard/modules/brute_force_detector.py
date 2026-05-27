"""
Extreme IP Guard - Brute Force Detection Module
Detects credential stuffing, password spraying, and targeted
brute force attacks across multiple authentication vectors.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from config.settings import settings


@dataclass
class AuthAttempt:
    timestamp: float
    username: str
    success: bool
    service: str
    source_port: int = 0


@dataclass
class AttackProfile:
    attempts: List[AuthAttempt] = field(default_factory=list)
    unique_usernames: Set[str] = field(default_factory=set)
    unique_services: Set[str] = field(default_factory=set)
    failed_count: int = 0
    success_count: int = 0
    first_attempt: float = 0.0
    last_attempt: float = 0.0
    is_locked: bool = False
    lock_until: float = 0.0


class BruteForceDetector:
    """
    Detects brute force attack patterns:
    - Single-target: many passwords against one account
    - Password spraying: one password against many accounts
    - Credential stuffing: known credential pairs
    - Distributed brute force: coordinated from multiple IPs
    - Service-specific: SSH, RDP, HTTP auth, API keys
    """

    LOCKOUT_ESCALATION = [60, 300, 900, 3600, 86400]

    def __init__(self):
        self._profiles: Dict[str, AttackProfile] = defaultdict(AttackProfile)
        self._username_tracker: Dict[str, Set[str]] = defaultdict(set)
        self._service_tracker: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._detections: List[dict] = []

    def record_auth_attempt(
        self,
        source_ip: str,
        username: str,
        success: bool,
        service: str = "ssh",
        source_port: int = 0,
    ) -> dict:
        now = time.monotonic()
        profile = self._profiles[source_ip]

        if profile.is_locked and now < profile.lock_until:
            return {
                "allowed": False,
                "reason": "ip_locked",
                "retry_after": int(profile.lock_until - now),
                "ip": source_ip,
            }

        if profile.is_locked and now >= profile.lock_until:
            profile.is_locked = False

        attempt = AuthAttempt(
            timestamp=now,
            username=username,
            success=success,
            service=service,
            source_port=source_port,
        )

        if not profile.first_attempt:
            profile.first_attempt = now
        profile.last_attempt = now

        profile.attempts.append(attempt)
        profile.unique_usernames.add(username)
        profile.unique_services.add(service)

        if success:
            profile.success_count += 1
        else:
            profile.failed_count += 1

        self._username_tracker[username].add(source_ip)
        self._service_tracker[service][source_ip] += 1

        window = settings.BRUTE_FORCE_WINDOW
        cutoff = now - window
        profile.attempts = [a for a in profile.attempts if a.timestamp > cutoff]
        recent_failures = sum(1 for a in profile.attempts if not a.success)

        result = {"allowed": True, "detection": None, "ip": source_ip}

        if recent_failures >= settings.BRUTE_FORCE_THRESHOLD:
            attack_type = self._classify_attack(profile, source_ip)
            severity = self._assess_severity(profile, attack_type)

            lockout_index = min(
                profile.failed_count // settings.BRUTE_FORCE_THRESHOLD,
                len(self.LOCKOUT_ESCALATION) - 1
            )
            lockout_duration = self.LOCKOUT_ESCALATION[lockout_index]

            profile.is_locked = True
            profile.lock_until = now + lockout_duration

            detection = {
                "detected": True,
                "source_ip": source_ip,
                "attack_type": attack_type,
                "severity": severity,
                "failed_attempts": recent_failures,
                "unique_usernames": len(profile.unique_usernames),
                "unique_services": len(profile.unique_services),
                "lockout_duration": lockout_duration,
                "usernames_targeted": list(profile.unique_usernames)[:20],
                "services_targeted": list(profile.unique_services),
                "timestamp": now,
            }

            self._detections.append(detection)
            if len(self._detections) > 10000:
                self._detections = self._detections[-5000:]

            result = {
                "allowed": False,
                "reason": "brute_force_detected",
                "detection": detection,
                "ip": source_ip,
            }

        return result

    def _classify_attack(self, profile: AttackProfile, source_ip: str) -> str:
        if len(profile.unique_usernames) == 1:
            return "targeted_brute_force"

        if len(profile.unique_usernames) > 5 and profile.failed_count > 20:
            recent_usernames = [a.username for a in profile.attempts[-20:]]
            unique_recent = set(recent_usernames)
            if len(unique_recent) > len(recent_usernames) * 0.7:
                return "credential_stuffing"

        if len(profile.unique_usernames) > 10:
            return "password_spraying"

        for username, ips in self._username_tracker.items():
            if source_ip in ips and len(ips) > 5:
                return "distributed_brute_force"

        return "brute_force"

    def _assess_severity(self, profile: AttackProfile, attack_type: str) -> str:
        if attack_type in ("credential_stuffing", "distributed_brute_force"):
            return "critical"
        if profile.failed_count > 50 or attack_type == "password_spraying":
            return "high"
        if profile.failed_count > 20:
            return "medium"
        return "low"

    def check_password_spraying(self, threshold: int = 5) -> List[dict]:
        alerts = []
        for username, ips in self._username_tracker.items():
            if len(ips) >= threshold:
                alerts.append({
                    "type": "password_spraying",
                    "username": username,
                    "unique_sources": len(ips),
                    "source_ips": list(ips)[:20],
                    "severity": "high" if len(ips) > 20 else "medium",
                })
        return alerts

    def get_locked_ips(self) -> List[dict]:
        now = time.monotonic()
        return [
            {
                "ip": ip,
                "locked_until": round(p.lock_until - now, 0),
                "failed_attempts": p.failed_count,
            }
            for ip, p in self._profiles.items()
            if p.is_locked and now < p.lock_until
        ]

    def unlock_ip(self, ip: str) -> bool:
        if ip in self._profiles:
            self._profiles[ip].is_locked = False
            self._profiles[ip].lock_until = 0
            return True
        return False

    def get_recent_detections(self, limit: int = 50) -> List[dict]:
        return self._detections[-limit:]

    def cleanup(self):
        now = time.monotonic()
        stale = settings.BRUTE_FORCE_WINDOW * 5
        stale_ips = [
            ip for ip, p in self._profiles.items()
            if now - p.last_attempt > stale and not p.is_locked
        ]
        for ip in stale_ips:
            del self._profiles[ip]

    def get_stats(self) -> dict:
        now = time.monotonic()
        return {
            "tracked_ips": len(self._profiles),
            "locked_ips": sum(
                1 for p in self._profiles.values()
                if p.is_locked and now < p.lock_until
            ),
            "total_detections": len(self._detections),
            "tracked_usernames": len(self._username_tracker),
        }


brute_force_detector = BruteForceDetector()

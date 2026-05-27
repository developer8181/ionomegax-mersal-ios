"""
Extreme IP Guard - Advanced Threat Detection Engine
AI-powered threat analysis with behavioral pattern recognition.
"""

import asyncio
import ipaddress
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
from config.settings import settings


@dataclass
class ConnectionProfile:
    ip: str
    first_seen: float = field(default_factory=time.time)
    request_timestamps: List[float] = field(default_factory=list)
    ports_accessed: set = field(default_factory=set)
    methods_used: set = field(default_factory=set)
    paths_accessed: List[str] = field(default_factory=list)
    user_agents: set = field(default_factory=set)
    failed_attempts: int = 0
    total_bytes: int = 0
    anomaly_score: float = 0.0
    threat_indicators: List[str] = field(default_factory=list)


class ThreatEngine:
    """Neural-inspired threat detection with multi-vector analysis."""

    SUSPICIOUS_PORTS = {
        22, 23, 25, 445, 1433, 1434, 3306, 3389, 5432, 5900,
        6379, 8080, 8443, 9200, 27017, 11211
    }

    MALICIOUS_PATTERNS = [
        "/../", "/etc/passwd", "/etc/shadow", "cmd.exe", "powershell",
        "<script>", "UNION SELECT", "OR 1=1", "DROP TABLE",
        "/wp-admin", "/phpmyadmin", "/.env", "/config.php",
        "/shell", "/backdoor", "/c99", "/r57",
        "eval(", "exec(", "system(", "passthru(",
    ]

    KNOWN_BOT_SIGNATURES = [
        "sqlmap", "nikto", "nmap", "masscan", "zgrab",
        "nuclei", "dirbuster", "gobuster", "hydra", "medusa",
    ]

    def __init__(self):
        self.profiles: Dict[str, ConnectionProfile] = {}
        self.blocked_ips: set = set()
        self.whitelisted_ips: set = {"127.0.0.1", "::1"}
        self.threat_cache: Dict[str, Tuple[float, float]] = {}
        self._lock = asyncio.Lock()

    def get_profile(self, ip: str) -> ConnectionProfile:
        if ip not in self.profiles:
            self.profiles[ip] = ConnectionProfile(ip=ip)
        return self.profiles[ip]

    async def analyze_request(
        self,
        source_ip: str,
        dest_port: int = 80,
        method: str = "GET",
        path: str = "/",
        user_agent: str = "",
        payload_size: int = 0,
    ) -> Dict:
        if source_ip in self.whitelisted_ips:
            return {"threat_score": 0, "threat_level": "safe", "action": "allow", "indicators": []}

        profile = self.get_profile(source_ip)
        now = time.time()

        profile.request_timestamps.append(now)
        profile.ports_accessed.add(dest_port)
        profile.methods_used.add(method)
        profile.paths_accessed.append(path)
        if user_agent:
            profile.user_agents.add(user_agent)
        profile.total_bytes += payload_size

        cutoff = now - 60
        profile.request_timestamps = [t for t in profile.request_timestamps if t > cutoff]

        indicators = []
        scores = []

        rate_score = self._analyze_rate(profile, now)
        if rate_score > 0:
            indicators.append(f"High request rate: {len(profile.request_timestamps)}/min")
            scores.append(rate_score)

        port_score = self._analyze_ports(profile)
        if port_score > 0:
            indicators.append(f"Suspicious port scanning: {len(profile.ports_accessed)} ports")
            scores.append(port_score)

        payload_score = self._analyze_payload(path, user_agent)
        if payload_score > 0:
            indicators.append("Malicious payload patterns detected")
            scores.append(payload_score)

        bot_score = self._analyze_bot_signatures(user_agent)
        if bot_score > 0:
            indicators.append(f"Known attack tool detected: {user_agent[:50]}")
            scores.append(bot_score)

        behavioral_score = self._analyze_behavior(profile)
        if behavioral_score > 0:
            indicators.append("Anomalous behavioral pattern")
            scores.append(behavioral_score)

        ip_score = self._analyze_ip_reputation(source_ip)
        if ip_score > 0:
            indicators.append("IP in suspicious range")
            scores.append(ip_score)

        final_score = min(100, sum(scores))
        profile.anomaly_score = final_score
        profile.threat_indicators = indicators

        threat_level = self._score_to_level(final_score)
        action = self._determine_action(final_score, source_ip)

        return {
            "threat_score": round(final_score, 2),
            "threat_level": threat_level,
            "action": action,
            "indicators": indicators,
            "request_rate": len(profile.request_timestamps),
            "ports_scanned": len(profile.ports_accessed),
            "profile_age_seconds": int(now - profile.first_seen),
        }

    def _analyze_rate(self, profile: ConnectionProfile, now: float) -> float:
        rpm = len(profile.request_timestamps)
        if rpm > settings.DDOS_THRESHOLD:
            return 40.0
        elif rpm > settings.MAX_REQUESTS_PER_MINUTE:
            return 25.0
        elif rpm > settings.MAX_REQUESTS_PER_MINUTE * 0.7:
            return 10.0
        return 0.0

    def _analyze_ports(self, profile: ConnectionProfile) -> float:
        suspicious_hits = profile.ports_accessed & self.SUSPICIOUS_PORTS
        if len(profile.ports_accessed) > 10:
            return 35.0
        elif len(suspicious_hits) > 3:
            return 25.0
        elif len(suspicious_hits) > 0:
            return 10.0
        return 0.0

    def _analyze_payload(self, path: str, user_agent: str) -> float:
        combined = (path + user_agent).lower()
        matches = sum(1 for p in self.MALICIOUS_PATTERNS if p.lower() in combined)
        if matches >= 3:
            return 45.0
        elif matches >= 2:
            return 30.0
        elif matches >= 1:
            return 15.0
        return 0.0

    def _analyze_bot_signatures(self, user_agent: str) -> float:
        ua_lower = user_agent.lower()
        for sig in self.KNOWN_BOT_SIGNATURES:
            if sig in ua_lower:
                return 40.0
        return 0.0

    def _analyze_behavior(self, profile: ConnectionProfile) -> float:
        score = 0.0
        if len(profile.paths_accessed) > 50:
            unique_ratio = len(set(profile.paths_accessed)) / len(profile.paths_accessed)
            if unique_ratio > 0.9:
                score += 20.0

        if len(profile.user_agents) > 5:
            score += 15.0

        if profile.failed_attempts > 10:
            score += 25.0
        elif profile.failed_attempts > 5:
            score += 15.0

        return min(score, 35.0)

    def _analyze_ip_reputation(self, ip: str) -> float:
        try:
            addr = ipaddress.ip_address(ip)
            if addr.is_private or addr.is_loopback:
                return 0.0
            if addr.is_reserved:
                return 5.0
        except ValueError:
            return 10.0
        return 0.0

    def _score_to_level(self, score: float) -> str:
        if score >= settings.THREAT_SCORE_CRITICAL:
            return "critical"
        elif score >= settings.THREAT_SCORE_HIGH:
            return "high"
        elif score >= settings.THREAT_SCORE_MEDIUM:
            return "medium"
        elif score >= settings.THREAT_SCORE_LOW:
            return "low"
        return "safe"

    def _determine_action(self, score: float, ip: str) -> str:
        if ip in self.blocked_ips:
            return "block"
        if settings.AUTO_BLOCK_ENABLED and score >= settings.AUTO_BLOCK_THRESHOLD:
            self.blocked_ips.add(ip)
            return "block"
        if score >= settings.THREAT_SCORE_HIGH:
            return "challenge"
        if score >= settings.THREAT_SCORE_MEDIUM:
            return "rate_limit"
        if score >= settings.THREAT_SCORE_LOW:
            return "log"
        return "allow"

    def get_stats(self) -> Dict:
        total = len(self.profiles)
        blocked = len(self.blocked_ips)
        critical = sum(1 for p in self.profiles.values() if p.anomaly_score >= settings.THREAT_SCORE_CRITICAL)
        high = sum(1 for p in self.profiles.values() if settings.THREAT_SCORE_HIGH <= p.anomaly_score < settings.THREAT_SCORE_CRITICAL)
        return {
            "total_tracked": total,
            "blocked": blocked,
            "whitelisted": len(self.whitelisted_ips),
            "critical_threats": critical,
            "high_threats": high,
            "engine_uptime": time.time(),
        }


threat_engine = ThreatEngine()

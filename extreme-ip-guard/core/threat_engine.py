"""
Extreme IP Guard - Threat Intelligence Engine
Core analysis engine that computes threat scores, correlates events,
and determines the risk profile of IP addresses in real-time.
"""

import asyncio
import ipaddress
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import (
    IPAddress, ThreatEvent, ThreatLevel, IPStatus,
    ActionType, EventType
)
from config.settings import settings


class ThreatIntelligenceEngine:
    """
    Multi-layered threat analysis engine that combines behavioral analysis,
    reputation scoring, pattern detection, and heuristic evaluation to
    produce a comprehensive threat profile for each IP address.
    """

    PRIVATE_RANGES = [
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
    ]

    RISK_WEIGHTS = {
        "tor_exit": 25.0,
        "vpn": 10.0,
        "proxy": 15.0,
        "datacenter": 8.0,
        "bot": 20.0,
        "port_scan": 30.0,
        "brute_force": 35.0,
        "ddos": 40.0,
        "malware": 45.0,
        "anomaly": 15.0,
        "high_request_rate": 12.0,
        "known_threat_feed": 30.0,
        "bad_country_reputation": 5.0,
        "data_exfiltration": 40.0,
        "reconnaissance": 20.0,
    }

    DECAY_HALF_LIFE_HOURS = 72

    def __init__(self):
        self._event_buffer: Dict[str, List[dict]] = defaultdict(list)
        self._threat_cache: Dict[str, Tuple[float, datetime]] = {}
        self._known_threats: set = set()
        self._whitelist: set = set()

    def is_private_ip(self, ip_str: str) -> bool:
        try:
            addr = ipaddress.ip_address(ip_str)
            return any(addr in net for net in self.PRIVATE_RANGES)
        except ValueError:
            return False

    async def analyze_ip(self, ip_str: str, db: AsyncSession) -> dict:
        """Full threat analysis pipeline for a single IP."""
        result = await db.execute(
            select(IPAddress).where(IPAddress.ip == ip_str)
        )
        ip_record = result.scalar_one_or_none()

        if not ip_record:
            ip_record = IPAddress(
                ip=ip_str,
                version=4 if "." in ip_str else 6,
            )
            db.add(ip_record)
            await db.flush()

        risk_factors = []
        base_score = 0.0

        if ip_record.is_tor:
            base_score += self.RISK_WEIGHTS["tor_exit"]
            risk_factors.append("TOR exit node detected")
        if ip_record.is_vpn:
            base_score += self.RISK_WEIGHTS["vpn"]
            risk_factors.append("VPN endpoint detected")
        if ip_record.is_proxy:
            base_score += self.RISK_WEIGHTS["proxy"]
            risk_factors.append("Open proxy detected")
        if ip_record.is_datacenter:
            base_score += self.RISK_WEIGHTS["datacenter"]
            risk_factors.append("Datacenter IP range")
        if ip_record.is_bot:
            base_score += self.RISK_WEIGHTS["bot"]
            risk_factors.append("Automated bot behavior")

        event_score, event_factors = await self._analyze_events(ip_record.id, db)
        base_score += event_score
        risk_factors.extend(event_factors)

        behavioral_score, behavioral_factors = await self._behavioral_analysis(ip_record, db)
        base_score += behavioral_score
        risk_factors.extend(behavioral_factors)

        if ip_str in self._known_threats:
            base_score += self.RISK_WEIGHTS["known_threat_feed"]
            risk_factors.append("Listed in threat intelligence feeds")

        decay = self._calculate_decay(ip_record.last_seen)
        final_score = min(100.0, base_score * decay)

        threat_level = self._score_to_level(final_score)

        recommendations = self._generate_recommendations(
            final_score, risk_factors, ip_record
        )

        ip_record.threat_score = final_score
        ip_record.reputation_score = max(0, 100.0 - final_score)
        await db.commit()

        self._threat_cache[ip_str] = (final_score, datetime.now(timezone.utc))

        return {
            "ip": ip_str,
            "threat_score": round(final_score, 2),
            "reputation_score": round(max(0, 100.0 - final_score), 2),
            "threat_level": threat_level.value,
            "risk_factors": risk_factors,
            "geo_info": {
                "country": ip_record.country,
                "city": ip_record.city,
                "latitude": ip_record.latitude,
                "longitude": ip_record.longitude,
            },
            "network_info": {
                "asn": ip_record.asn,
                "org": ip_record.org,
                "isp": ip_record.isp,
                "is_vpn": ip_record.is_vpn,
                "is_tor": ip_record.is_tor,
                "is_proxy": ip_record.is_proxy,
            },
            "behavioral_analysis": {
                "total_requests": ip_record.total_requests,
                "blocked_requests": ip_record.blocked_requests,
                "block_ratio": (
                    ip_record.blocked_requests / max(1, ip_record.total_requests)
                ),
            },
            "recommendations": recommendations,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _analyze_events(
        self, ip_id: int, db: AsyncSession
    ) -> Tuple[float, List[str]]:
        score = 0.0
        factors = []
        window = datetime.now(timezone.utc) - timedelta(hours=24)

        result = await db.execute(
            select(ThreatEvent.event_type, func.count(ThreatEvent.id))
            .where(and_(ThreatEvent.ip_id == ip_id, ThreatEvent.timestamp >= window))
            .group_by(ThreatEvent.event_type)
        )
        event_counts = {row[0]: row[1] for row in result.all()}

        event_scoring = {
            EventType.PORT_SCAN: ("port_scan", "Port scanning activity ({count} events)"),
            EventType.BRUTE_FORCE: ("brute_force", "Brute force attempts ({count} events)"),
            EventType.DDOS: ("ddos", "DDoS attack patterns ({count} events)"),
            EventType.MALWARE: ("malware", "Malware signatures detected ({count} events)"),
            EventType.ANOMALY: ("anomaly", "Anomalous behavior ({count} events)"),
            EventType.DATA_EXFILTRATION: ("data_exfiltration", "Data exfiltration attempt ({count} events)"),
            EventType.RECONNAISSANCE: ("reconnaissance", "Network reconnaissance ({count} events)"),
        }

        for event_type, (weight_key, desc_template) in event_scoring.items():
            count = event_counts.get(event_type, 0)
            if count > 0:
                multiplier = min(3.0, 1.0 + math.log2(max(1, count)))
                score += self.RISK_WEIGHTS[weight_key] * multiplier
                factors.append(desc_template.format(count=count))

        return score, factors

    async def _behavioral_analysis(
        self, ip_record: IPAddress, db: AsyncSession
    ) -> Tuple[float, List[str]]:
        score = 0.0
        factors = []

        if ip_record.total_requests > 0:
            block_ratio = ip_record.blocked_requests / ip_record.total_requests
            if block_ratio > 0.5:
                score += 15.0
                factors.append(f"High block ratio: {block_ratio:.1%}")

        if ip_record.total_requests > settings.RATE_LIMIT_MAX_REQUESTS * 10:
            score += self.RISK_WEIGHTS["high_request_rate"]
            factors.append("Extremely high request volume")

        return score, factors

    def _calculate_decay(self, last_seen: Optional[datetime]) -> float:
        if not last_seen:
            return 1.0
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)
        hours_elapsed = (datetime.now(timezone.utc) - last_seen).total_seconds() / 3600
        return math.pow(0.5, hours_elapsed / self.DECAY_HALF_LIFE_HOURS)

    def _score_to_level(self, score: float) -> ThreatLevel:
        if score >= 90:
            return ThreatLevel.CRITICAL
        elif score >= 70:
            return ThreatLevel.HIGH
        elif score >= 45:
            return ThreatLevel.MEDIUM
        elif score >= 20:
            return ThreatLevel.LOW
        elif score >= 5:
            return ThreatLevel.INFO
        return ThreatLevel.SAFE

    def _generate_recommendations(
        self, score: float, factors: List[str], ip_record: IPAddress
    ) -> List[str]:
        recs = []
        if score >= settings.AUTO_BLOCK_THRESHOLD:
            recs.append("IMMEDIATE: Auto-block this IP address")
            recs.append("Add to permanent blocklist")
        elif score >= settings.THREAT_SCORE_THRESHOLD:
            recs.append("Enable enhanced monitoring for this IP")
            recs.append("Apply rate limiting")
            recs.append("Consider temporary quarantine")
        elif score >= 45:
            recs.append("Monitor traffic patterns from this IP")
            recs.append("Log all requests for forensic analysis")
        elif score >= 20:
            recs.append("Standard monitoring sufficient")

        if ip_record.is_tor:
            recs.append("Consider blocking TOR exit nodes if not required")
        if ip_record.is_proxy:
            recs.append("Validate proxy usage against access policy")

        return recs

    async def process_event(
        self, ip_str: str, event_type: EventType, db: AsyncSession, **kwargs
    ) -> dict:
        """Process an incoming security event and update threat assessment."""
        result = await db.execute(
            select(IPAddress).where(IPAddress.ip == ip_str)
        )
        ip_record = result.scalar_one_or_none()

        if not ip_record:
            ip_record = IPAddress(
                ip=ip_str,
                version=4 if "." in ip_str else 6,
            )
            db.add(ip_record)
            await db.flush()

        ip_record.total_requests = (ip_record.total_requests or 0) + 1
        ip_record.last_seen = datetime.now(timezone.utc)

        threat_level = self._event_type_to_threat_level(event_type)

        event = ThreatEvent(
            ip_id=ip_record.id,
            event_type=event_type,
            threat_level=threat_level,
            description=kwargs.get("description"),
            source_port=kwargs.get("source_port"),
            destination_port=kwargs.get("destination_port"),
            protocol=kwargs.get("protocol"),
            signature=kwargs.get("signature"),
            raw_data=kwargs.get("raw_data"),
        )
        db.add(event)

        analysis = await self.analyze_ip(ip_str, db)

        action = self._determine_action(analysis["threat_score"], ip_record)
        event.action_taken = action

        if action == ActionType.BLOCK:
            ip_record.status = IPStatus.BLOCKED
            ip_record.blocked_requests = (ip_record.blocked_requests or 0) + 1
        elif action == ActionType.QUARANTINE:
            ip_record.status = IPStatus.QUARANTINED

        await db.commit()

        return {
            "event_id": event.id,
            "ip": ip_str,
            "event_type": event_type.value,
            "threat_level": threat_level.value,
            "threat_score": analysis["threat_score"],
            "action_taken": action.value,
            "analysis": analysis,
        }

    def _event_type_to_threat_level(self, event_type: EventType) -> ThreatLevel:
        mapping = {
            EventType.CONNECTION: ThreatLevel.INFO,
            EventType.PORT_SCAN: ThreatLevel.HIGH,
            EventType.BRUTE_FORCE: ThreatLevel.HIGH,
            EventType.DDOS: ThreatLevel.CRITICAL,
            EventType.ANOMALY: ThreatLevel.MEDIUM,
            EventType.POLICY_VIOLATION: ThreatLevel.MEDIUM,
            EventType.MALWARE: ThreatLevel.CRITICAL,
            EventType.DATA_EXFILTRATION: ThreatLevel.CRITICAL,
            EventType.RECONNAISSANCE: ThreatLevel.MEDIUM,
            EventType.LATERAL_MOVEMENT: ThreatLevel.HIGH,
        }
        return mapping.get(event_type, ThreatLevel.INFO)

    def _determine_action(self, threat_score: float, ip_record: IPAddress) -> ActionType:
        if ip_record.status == IPStatus.WHITELISTED:
            return ActionType.LOG

        if threat_score >= settings.AUTO_BLOCK_THRESHOLD:
            return ActionType.BLOCK
        elif threat_score >= settings.THREAT_SCORE_THRESHOLD:
            return ActionType.QUARANTINE
        elif threat_score >= 45:
            return ActionType.RATE_LIMIT
        elif threat_score >= 20:
            return ActionType.ALERT
        return ActionType.LOG

    def update_threat_feeds(self, threat_ips: set):
        self._known_threats = threat_ips

    def update_whitelist(self, whitelist_ips: set):
        self._whitelist = whitelist_ips


threat_engine = ThreatIntelligenceEngine()

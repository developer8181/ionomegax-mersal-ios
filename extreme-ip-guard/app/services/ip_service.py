"""
Extreme IP Guard - IP Management Service
CRUD operations and business logic for IP management.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict
from sqlalchemy import select, func, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    MonitoredIP, TrafficLog, Alert, FirewallRule,
    SystemEvent, NetworkScan, ThreatLevel, IPStatus,
    AlertType, RuleAction
)
from app.core.threat_engine import threat_engine
from app.core.ip_intelligence import ip_intel_service


class IPService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_ips(self, limit: int = 100, offset: int = 0, status: Optional[str] = None) -> List[MonitoredIP]:
        query = select(MonitoredIP).order_by(MonitoredIP.threat_score.desc())
        if status:
            query = query.where(MonitoredIP.status == status)
        query = query.limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_ip_by_address(self, ip_address: str) -> Optional[MonitoredIP]:
        result = await self.db.execute(
            select(MonitoredIP).where(MonitoredIP.ip_address == ip_address)
        )
        return result.scalar_one_or_none()

    async def get_ip_by_id(self, ip_id: int) -> Optional[MonitoredIP]:
        result = await self.db.execute(
            select(MonitoredIP).where(MonitoredIP.id == ip_id)
        )
        return result.scalar_one_or_none()

    async def add_ip(self, ip_address: str, notes: str = None) -> MonitoredIP:
        existing = await self.get_ip_by_address(ip_address)
        if existing:
            return existing

        intel = await ip_intel_service.analyze(ip_address)

        ip_record = MonitoredIP(
            ip_address=ip_address,
            hostname=intel.hostname,
            status=IPStatus.MONITORING,
            threat_level=ThreatLevel.SAFE,
            threat_score=intel.risk_score,
            reputation_score=max(0, 100 - intel.risk_score),
            country=intel.country,
            country_code=intel.country_code,
            city=intel.city,
            latitude=intel.latitude,
            longitude=intel.longitude,
            asn=intel.asn,
            org=intel.org,
            isp=intel.isp,
            is_vpn=intel.is_vpn,
            is_proxy=intel.is_proxy,
            is_tor=intel.is_tor,
            is_bot=intel.is_bot,
            notes=notes,
        )

        self.db.add(ip_record)
        await self.db.commit()
        await self.db.refresh(ip_record)
        return ip_record

    async def update_ip_status(self, ip_id: int, status: IPStatus) -> Optional[MonitoredIP]:
        ip_record = await self.get_ip_by_id(ip_id)
        if not ip_record:
            return None

        ip_record.status = status
        ip_record.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(ip_record)
        return ip_record

    async def block_ip(self, ip_id: int) -> Optional[MonitoredIP]:
        ip_record = await self.get_ip_by_id(ip_id)
        if not ip_record:
            return None

        ip_record.status = IPStatus.BLOCKED
        ip_record.updated_at = datetime.now(timezone.utc)
        threat_engine.blocked_ips.add(ip_record.ip_address)

        await self._create_system_event(
            "ip_blocked",
            ThreatLevel.HIGH,
            f"IP {ip_record.ip_address} has been blocked",
            f"Country: {ip_record.country}, Threat Score: {ip_record.threat_score}"
        )

        await self.db.commit()
        await self.db.refresh(ip_record)
        return ip_record

    async def unblock_ip(self, ip_id: int) -> Optional[MonitoredIP]:
        ip_record = await self.get_ip_by_id(ip_id)
        if not ip_record:
            return None

        ip_record.status = IPStatus.MONITORING
        ip_record.updated_at = datetime.now(timezone.utc)
        threat_engine.blocked_ips.discard(ip_record.ip_address)

        await self.db.commit()
        await self.db.refresh(ip_record)
        return ip_record

    async def whitelist_ip(self, ip_id: int) -> Optional[MonitoredIP]:
        ip_record = await self.get_ip_by_id(ip_id)
        if not ip_record:
            return None

        ip_record.status = IPStatus.WHITELISTED
        ip_record.threat_score = 0
        ip_record.threat_level = ThreatLevel.SAFE
        ip_record.updated_at = datetime.now(timezone.utc)
        threat_engine.whitelisted_ips.add(ip_record.ip_address)

        await self.db.commit()
        await self.db.refresh(ip_record)
        return ip_record

    async def delete_ip(self, ip_id: int) -> bool:
        ip_record = await self.get_ip_by_id(ip_id)
        if not ip_record:
            return False

        await self.db.delete(ip_record)
        await self.db.commit()
        return True

    async def get_dashboard_stats(self) -> Dict:
        total = await self.db.execute(select(func.count(MonitoredIP.id)))
        blocked = await self.db.execute(
            select(func.count(MonitoredIP.id)).where(MonitoredIP.status == IPStatus.BLOCKED)
        )
        whitelisted = await self.db.execute(
            select(func.count(MonitoredIP.id)).where(MonitoredIP.status == IPStatus.WHITELISTED)
        )
        critical = await self.db.execute(
            select(func.count(MonitoredIP.id)).where(MonitoredIP.threat_level == ThreatLevel.CRITICAL)
        )
        high = await self.db.execute(
            select(func.count(MonitoredIP.id)).where(MonitoredIP.threat_level == ThreatLevel.HIGH)
        )
        active_alerts = await self.db.execute(
            select(func.count(Alert.id)).where(Alert.is_resolved == False)
        )
        total_alerts = await self.db.execute(select(func.count(Alert.id)))
        active_rules = await self.db.execute(
            select(func.count(FirewallRule.id)).where(FirewallRule.is_active == True)
        )

        top_threats = await self.db.execute(
            select(MonitoredIP)
            .where(MonitoredIP.threat_score > 0)
            .order_by(MonitoredIP.threat_score.desc())
            .limit(10)
        )

        recent_alerts = await self.db.execute(
            select(Alert)
            .order_by(Alert.created_at.desc())
            .limit(10)
        )

        country_stats = await self.db.execute(
            select(
                MonitoredIP.country_code,
                MonitoredIP.country,
                func.count(MonitoredIP.id).label('count')
            )
            .group_by(MonitoredIP.country_code, MonitoredIP.country)
            .order_by(func.count(MonitoredIP.id).desc())
            .limit(15)
        )

        threat_distribution = await self.db.execute(
            select(
                MonitoredIP.threat_level,
                func.count(MonitoredIP.id).label('count')
            )
            .group_by(MonitoredIP.threat_level)
        )

        return {
            "total_ips": total.scalar() or 0,
            "blocked_ips": blocked.scalar() or 0,
            "whitelisted_ips": whitelisted.scalar() or 0,
            "critical_threats": critical.scalar() or 0,
            "high_threats": high.scalar() or 0,
            "active_alerts": active_alerts.scalar() or 0,
            "total_alerts": total_alerts.scalar() or 0,
            "active_rules": active_rules.scalar() or 0,
            "top_threats": [
                {
                    "id": ip.id, "ip": ip.ip_address, "score": ip.threat_score,
                    "level": ip.threat_level.value if ip.threat_level else "safe",
                    "country": ip.country, "country_code": ip.country_code,
                }
                for ip in top_threats.scalars().all()
            ],
            "recent_alerts": [
                {
                    "id": a.id, "type": a.alert_type.value if a.alert_type else "",
                    "level": a.threat_level.value if a.threat_level else "",
                    "title": a.title, "source_ip": a.source_ip,
                    "created_at": a.created_at.isoformat() if a.created_at else "",
                    "is_resolved": a.is_resolved,
                }
                for a in recent_alerts.scalars().all()
            ],
            "country_distribution": [
                {"code": row[0], "country": row[1], "count": row[2]}
                for row in country_stats.all()
            ],
            "threat_distribution": [
                {"level": row[0].value if row[0] else "unknown", "count": row[1]}
                for row in threat_distribution.all()
            ],
            "engine_stats": threat_engine.get_stats(),
        }

    async def get_alerts(self, limit: int = 50, unresolved_only: bool = False) -> List[Alert]:
        query = select(Alert).order_by(Alert.created_at.desc())
        if unresolved_only:
            query = query.where(Alert.is_resolved == False)
        query = query.limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_alert(
        self, alert_type: AlertType, title: str, description: str,
        source_ip: str = None, threat_level: ThreatLevel = ThreatLevel.MEDIUM,
        ip_id: int = None
    ) -> Alert:
        alert = Alert(
            ip_id=ip_id,
            alert_type=alert_type,
            threat_level=threat_level,
            title=title,
            description=description,
            source_ip=source_ip,
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def resolve_alert(self, alert_id: int, resolved_by: str = "system") -> Optional[Alert]:
        result = await self.db.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            return None

        alert.is_resolved = True
        alert.resolved_by = resolved_by
        alert.resolved_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(alert)
        return alert

    async def get_firewall_rules(self, active_only: bool = True) -> List[FirewallRule]:
        query = select(FirewallRule).order_by(FirewallRule.priority)
        if active_only:
            query = query.where(FirewallRule.is_active == True)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create_firewall_rule(self, **kwargs) -> FirewallRule:
        rule = FirewallRule(**kwargs)
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def toggle_firewall_rule(self, rule_id: int) -> Optional[FirewallRule]:
        result = await self.db.execute(select(FirewallRule).where(FirewallRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return None

        rule.is_active = not rule.is_active
        rule.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(rule)
        return rule

    async def delete_firewall_rule(self, rule_id: int) -> bool:
        result = await self.db.execute(select(FirewallRule).where(FirewallRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if not rule:
            return False
        await self.db.delete(rule)
        await self.db.commit()
        return True

    async def get_system_events(self, limit: int = 50) -> List[SystemEvent]:
        result = await self.db.execute(
            select(SystemEvent).order_by(SystemEvent.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def _create_system_event(self, event_type: str, severity: ThreatLevel, message: str, details: str = None):
        event = SystemEvent(
            event_type=event_type,
            severity=severity,
            message=message,
            details=details,
            source="system",
        )
        self.db.add(event)

    async def seed_demo_data(self):
        """Populate database with realistic demo data for showcase."""
        import random

        demo_ips = [
            ("192.168.1.1", IPStatus.WHITELISTED, ThreatLevel.SAFE, 0, "Gateway"),
            ("10.0.0.1", IPStatus.WHITELISTED, ThreatLevel.SAFE, 0, "Internal DNS"),
            ("185.220.101.42", IPStatus.BLOCKED, ThreatLevel.CRITICAL, 95, "Known Tor exit"),
            ("45.33.32.156", IPStatus.MONITORING, ThreatLevel.HIGH, 72, "Suspicious scanning"),
            ("203.0.113.50", IPStatus.MONITORING, ThreatLevel.MEDIUM, 45, "Elevated traffic"),
            ("198.51.100.23", IPStatus.QUARANTINED, ThreatLevel.HIGH, 78, "Brute force attempts"),
            ("91.108.56.100", IPStatus.MONITORING, ThreatLevel.LOW, 15, "Normal traffic"),
            ("104.16.132.229", IPStatus.MONITORING, ThreatLevel.SAFE, 5, "CDN traffic"),
            ("8.8.8.8", IPStatus.WHITELISTED, ThreatLevel.SAFE, 0, "Google DNS"),
            ("1.1.1.1", IPStatus.WHITELISTED, ThreatLevel.SAFE, 0, "Cloudflare DNS"),
            ("77.247.181.165", IPStatus.BLOCKED, ThreatLevel.CRITICAL, 92, "Tor relay node"),
            ("146.70.33.2", IPStatus.MONITORING, ThreatLevel.MEDIUM, 40, "VPN endpoint"),
            ("34.102.136.180", IPStatus.MONITORING, ThreatLevel.LOW, 12, "Cloud service"),
            ("172.67.182.31", IPStatus.MONITORING, ThreatLevel.SAFE, 3, "Cloudflare proxy"),
            ("52.84.150.100", IPStatus.MONITORING, ThreatLevel.LOW, 18, "AWS CloudFront"),
            ("185.199.108.153", IPStatus.MONITORING, ThreatLevel.SAFE, 2, "GitHub Pages"),
            ("199.249.230.80", IPStatus.BLOCKED, ThreatLevel.CRITICAL, 88, "Tor exit node"),
            ("103.86.96.100", IPStatus.MONITORING, ThreatLevel.MEDIUM, 35, "VPN provider"),
            ("62.210.105.116", IPStatus.BLOCKED, ThreatLevel.HIGH, 68, "Malicious scanner"),
            ("151.101.1.140", IPStatus.MONITORING, ThreatLevel.SAFE, 5, "Reddit CDN"),
        ]

        for ip_data in demo_ips:
            ip_addr, status, threat, score, notes = ip_data
            existing = await self.get_ip_by_address(ip_addr)
            if existing:
                continue

            intel = await ip_intel_service.analyze(ip_addr)
            ip_record = MonitoredIP(
                ip_address=ip_addr,
                hostname=intel.hostname,
                status=status,
                threat_level=threat,
                threat_score=score,
                reputation_score=max(0, 100 - score),
                country=intel.country,
                country_code=intel.country_code,
                city=intel.city,
                latitude=intel.latitude,
                longitude=intel.longitude,
                asn=intel.asn,
                org=intel.org,
                isp=intel.isp,
                is_vpn=intel.is_vpn,
                is_proxy=intel.is_proxy,
                is_tor=intel.is_tor,
                total_requests=random.randint(10, 50000),
                blocked_requests=random.randint(0, 1000),
                bytes_sent=random.randint(1000, 100000000),
                bytes_received=random.randint(1000, 100000000),
                notes=notes,
            )
            self.db.add(ip_record)

        alert_data = [
            (AlertType.DDOS_DETECTED, ThreatLevel.CRITICAL, "DDoS Attack Detected",
             "Volumetric DDoS attack from multiple sources targeting port 443", "185.220.101.42"),
            (AlertType.BRUTE_FORCE, ThreatLevel.HIGH, "SSH Brute Force Attempt",
             "Over 500 failed SSH login attempts in 10 minutes", "198.51.100.23"),
            (AlertType.PORT_SCAN, ThreatLevel.MEDIUM, "Sequential Port Scan",
             "Full TCP port scan detected from external IP", "45.33.32.156"),
            (AlertType.MALWARE_TRAFFIC, ThreatLevel.CRITICAL, "C2 Communication Detected",
             "Outbound traffic matching known C2 server patterns", "77.247.181.165"),
            (AlertType.INTRUSION_ATTEMPT, ThreatLevel.HIGH, "SQL Injection Attempt",
             "Multiple SQL injection payloads detected in HTTP requests", "62.210.105.116"),
            (AlertType.ANOMALY_DETECTED, ThreatLevel.MEDIUM, "Unusual Traffic Pattern",
             "300% increase in outbound traffic from internal host", "203.0.113.50"),
            (AlertType.GEO_ANOMALY, ThreatLevel.MEDIUM, "Geographic Anomaly",
             "Login attempt from unusual geographic location", "103.86.96.100"),
            (AlertType.RATE_LIMIT_EXCEEDED, ThreatLevel.LOW, "Rate Limit Exceeded",
             "API rate limit exceeded by 200% for this IP", "146.70.33.2"),
        ]

        for a_type, level, title, desc, src_ip in alert_data:
            alert = Alert(
                alert_type=a_type,
                threat_level=level,
                title=title,
                description=desc,
                source_ip=src_ip,
            )
            self.db.add(alert)

        rules_data = [
            ("Block Tor Exit Nodes", "Block all known Tor exit node IPs", "185.220.101.0/24",
             None, None, RuleAction.BLOCK, 10),
            ("Rate Limit API", "Limit API requests to 100/min", None,
             None, 443, RuleAction.RATE_LIMIT, 50),
            ("Allow Internal", "Allow all internal network traffic", "10.0.0.0/8",
             None, None, RuleAction.ALLOW, 1),
            ("Block Scanner IPs", "Block known vulnerability scanner IPs", "62.210.105.0/24",
             None, None, RuleAction.BLOCK, 20),
            ("Challenge Suspicious", "CAPTCHA challenge for suspicious traffic", None,
             None, 80, RuleAction.CHALLENGE, 60),
            ("Quarantine Malware", "Quarantine IPs with malware signatures", None,
             None, None, RuleAction.QUARANTINE, 15),
        ]

        for name, desc, cidr, src_ip, port, action, priority in rules_data:
            rule = FirewallRule(
                name=name,
                description=desc,
                source_cidr=cidr,
                source_ip=src_ip,
                destination_port=port,
                action=action,
                priority=priority,
                hit_count=random.randint(0, 10000),
            )
            self.db.add(rule)

        events_data = [
            ("system_start", ThreatLevel.INFO, "Extreme IP Guard engine initialized"),
            ("threat_detected", ThreatLevel.CRITICAL, "Critical threat level detected from 185.220.101.42"),
            ("auto_block", ThreatLevel.HIGH, "Auto-blocked IP 199.249.230.80 (threat score: 88)"),
            ("scan_complete", ThreatLevel.INFO, "Network scan completed: 20 devices analyzed"),
            ("rule_triggered", ThreatLevel.MEDIUM, "Firewall rule 'Block Tor Exit Nodes' triggered 150 times"),
            ("config_update", ThreatLevel.INFO, "Security policy updated: Auto-block threshold set to 75"),
        ]

        for etype, severity, msg in events_data:
            event = SystemEvent(event_type=etype, severity=severity, message=msg, source="system")
            self.db.add(event)

        await self.db.commit()

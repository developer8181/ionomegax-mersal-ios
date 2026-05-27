from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from .database import Base


class ThreatLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    SAFE = "safe"


class IPStatus(str, enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    WHITELISTED = "whitelisted"
    MONITORING = "monitoring"
    QUARANTINED = "quarantined"


class AlertType(str, enum.Enum):
    INTRUSION_ATTEMPT = "intrusion_attempt"
    DDOS_DETECTED = "ddos_detected"
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    MALWARE_TRAFFIC = "malware_traffic"
    ANOMALY_DETECTED = "anomaly_detected"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    GEO_ANOMALY = "geo_anomaly"
    REPUTATION_CHANGE = "reputation_change"
    POLICY_VIOLATION = "policy_violation"


class RuleAction(str, enum.Enum):
    ALLOW = "allow"
    BLOCK = "block"
    RATE_LIMIT = "rate_limit"
    REDIRECT = "redirect"
    LOG = "log"
    QUARANTINE = "quarantine"
    CHALLENGE = "challenge"


class MonitoredIP(Base):
    __tablename__ = "monitored_ips"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)
    hostname = Column(String(255), nullable=True)
    status = Column(SQLEnum(IPStatus), default=IPStatus.MONITORING)
    threat_level = Column(SQLEnum(ThreatLevel), default=ThreatLevel.SAFE)
    threat_score = Column(Float, default=0.0)
    reputation_score = Column(Float, default=50.0)

    country = Column(String(100), nullable=True)
    country_code = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    asn = Column(String(50), nullable=True)
    org = Column(String(255), nullable=True)
    isp = Column(String(255), nullable=True)

    total_requests = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)
    bytes_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)
    last_request_time = Column(DateTime, nullable=True)

    is_vpn = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_bot = Column(Boolean, default=False)

    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)

    traffic_logs = relationship("TrafficLog", back_populates="ip_record", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="ip_record", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_ip_status", "status"),
        Index("idx_ip_threat", "threat_level"),
        Index("idx_ip_score", "threat_score"),
    )


class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_id = Column(Integer, ForeignKey("monitored_ips.id"), nullable=False)
    source_ip = Column(String(45), nullable=False)
    destination_ip = Column(String(45), nullable=False)
    source_port = Column(Integer, nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(20), nullable=True)
    method = Column(String(10), nullable=True)
    path = Column(String(500), nullable=True)
    user_agent = Column(String(500), nullable=True)
    status_code = Column(Integer, nullable=True)
    bytes_transferred = Column(Integer, default=0)
    response_time = Column(Float, default=0.0)
    action_taken = Column(SQLEnum(RuleAction), default=RuleAction.ALLOW)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    ip_record = relationship("MonitoredIP", back_populates="traffic_logs")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_id = Column(Integer, ForeignKey("monitored_ips.id"), nullable=True)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    threat_level = Column(SQLEnum(ThreatLevel), default=ThreatLevel.MEDIUM)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_ip = Column(String(45), nullable=True)
    destination_ip = Column(String(45), nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    auto_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    ip_record = relationship("MonitoredIP", back_populates="alerts")

    __table_args__ = (
        Index("idx_alert_type", "alert_type"),
        Index("idx_alert_resolved", "is_resolved"),
    )


class FirewallRule(Base):
    __tablename__ = "firewall_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_ip = Column(String(45), nullable=True)
    source_cidr = Column(String(50), nullable=True)
    destination_port = Column(Integer, nullable=True)
    protocol = Column(String(20), nullable=True)
    action = Column(SQLEnum(RuleAction), default=RuleAction.BLOCK)
    priority = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    hit_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_rule_active", "is_active"),
        Index("idx_rule_priority", "priority"),
    )


class SystemEvent(Base):
    __tablename__ = "system_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)
    severity = Column(SQLEnum(ThreatLevel), default=ThreatLevel.INFO)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class NetworkScan(Base):
    __tablename__ = "network_scans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_type = Column(String(50), nullable=False)
    target = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")
    results = Column(Text, nullable=True)
    devices_found = Column(Integer, default=0)
    vulnerabilities_found = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

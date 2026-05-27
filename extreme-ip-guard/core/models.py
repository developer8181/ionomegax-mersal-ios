"""
Extreme IP Guard - Database Models
Complete data model for IP intelligence, threats, rules, and audit.
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    Enum, JSON, Index, BigInteger, ForeignKey
)
from sqlalchemy.orm import relationship
from core.database import Base


class ThreatLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    SAFE = "safe"


class IPStatus(str, enum.Enum):
    BLOCKED = "blocked"
    WHITELISTED = "whitelisted"
    MONITORED = "monitored"
    QUARANTINED = "quarantined"
    UNKNOWN = "unknown"


class ActionType(str, enum.Enum):
    BLOCK = "block"
    ALLOW = "allow"
    RATE_LIMIT = "rate_limit"
    QUARANTINE = "quarantine"
    ALERT = "alert"
    LOG = "log"
    CHALLENGE = "challenge"
    REDIRECT = "redirect"


class EventType(str, enum.Enum):
    CONNECTION = "connection"
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    DDOS = "ddos"
    ANOMALY = "anomaly"
    POLICY_VIOLATION = "policy_violation"
    MALWARE = "malware"
    DATA_EXFILTRATION = "data_exfiltration"
    RECONNAISSANCE = "reconnaissance"
    LATERAL_MOVEMENT = "lateral_movement"


def utcnow():
    return datetime.now(timezone.utc)


class IPAddress(Base):
    __tablename__ = "ip_addresses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip = Column(String(45), unique=True, nullable=False, index=True)
    version = Column(Integer, default=4)
    status = Column(Enum(IPStatus), default=IPStatus.UNKNOWN)
    threat_score = Column(Float, default=0.0)
    reputation_score = Column(Float, default=50.0)
    country = Column(String(3))
    city = Column(String(128))
    latitude = Column(Float)
    longitude = Column(Float)
    asn = Column(String(32))
    org = Column(String(256))
    isp = Column(String(256))
    is_vpn = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    is_bot = Column(Boolean, default=False)
    is_datacenter = Column(Boolean, default=False)
    total_requests = Column(BigInteger, default=0)
    blocked_requests = Column(BigInteger, default=0)
    first_seen = Column(DateTime, default=utcnow)
    last_seen = Column(DateTime, default=utcnow, onupdate=utcnow)
    tags = Column(JSON, default=list)
    metadata_ = Column("metadata", JSON, default=dict)

    events = relationship("ThreatEvent", back_populates="ip_address", lazy="dynamic")

    __table_args__ = (
        Index("idx_ip_threat", "threat_score"),
        Index("idx_ip_status", "status"),
        Index("idx_ip_country", "country"),
    )


class ThreatEvent(Base):
    __tablename__ = "threat_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ip_id = Column(Integer, ForeignKey("ip_addresses.id"), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    threat_level = Column(Enum(ThreatLevel), default=ThreatLevel.INFO)
    description = Column(Text)
    source_port = Column(Integer)
    destination_port = Column(Integer)
    protocol = Column(String(16))
    payload_hash = Column(String(64))
    signature = Column(String(256))
    action_taken = Column(Enum(ActionType))
    raw_data = Column(JSON)
    timestamp = Column(DateTime, default=utcnow, index=True)

    ip_address = relationship("IPAddress", back_populates="events")

    __table_args__ = (
        Index("idx_event_type_time", "event_type", "timestamp"),
        Index("idx_event_threat", "threat_level"),
    )


class SecurityRule(Base):
    __tablename__ = "security_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    rule_type = Column(String(64), nullable=False)
    conditions = Column(JSON, nullable=False)
    action = Column(Enum(ActionType), nullable=False)
    action_params = Column(JSON, default=dict)
    hit_count = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    __table_args__ = (
        Index("idx_rule_priority", "priority"),
        Index("idx_rule_enabled", "enabled"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    actor = Column(String(128))
    action = Column(String(64), nullable=False)
    target_type = Column(String(64))
    target_id = Column(String(128))
    details = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=utcnow, index=True)


class SystemMetrics(Base):
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(128), nullable=False)
    metric_value = Column(Float, nullable=False)
    tags = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=utcnow, index=True)

    __table_args__ = (
        Index("idx_metric_name_time", "metric_name", "timestamp"),
    )


class BlockList(Base):
    __tablename__ = "block_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    source_url = Column(String(1024))
    list_type = Column(String(32))
    entries_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=utcnow)
    enabled = Column(Boolean, default=True)
    entries = Column(JSON, default=list)

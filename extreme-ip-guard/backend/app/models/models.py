from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class ThreatLevel(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ThreatCategory(str, enum.Enum):
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    DDOS = "ddos"
    MALWARE = "malware"
    INTRUSION = "intrusion"
    DATA_EXFILTRATION = "data_exfiltration"
    ANOMALY = "anomaly"
    POLICY_VIOLATION = "policy_violation"
    RECONNAISSANCE = "reconnaissance"
    LATERAL_MOVEMENT = "lateral_movement"
    ZERO_DAY = "zero_day"


class PolicyAction(str, enum.Enum):
    ALLOW = "allow"
    BLOCK = "block"
    MONITOR = "monitor"
    ALERT = "alert"
    QUARANTINE = "quarantine"
    RATE_LIMIT = "rate_limit"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="analyst")  # admin, analyst, viewer
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255))
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class MonitoredIP(Base):
    __tablename__ = "monitored_ips"

    id = Column(String, primary_key=True, default=generate_uuid)
    ip_address = Column(String(45), nullable=False, index=True)
    hostname = Column(String(255))
    country = Column(String(100))
    country_code = Column(String(10))
    city = Column(String(100))
    asn = Column(String(100))
    organization = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)
    is_internal = Column(Boolean, default=False)
    is_trusted = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    risk_score = Column(Float, default=0.0)
    total_requests = Column(Integer, default=0)
    blocked_requests = Column(Integer, default=0)
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    tags = Column(JSON, default=list)
    metadata = Column(JSON, default=dict)

    threats = relationship("ThreatEvent", back_populates="source_ip_ref", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_monitored_ips_risk_score", "risk_score"),
        Index("ix_monitored_ips_last_seen", "last_seen"),
    )


class ThreatEvent(Base):
    __tablename__ = "threat_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_ip = Column(String(45), ForeignKey("monitored_ips.ip_address"), nullable=False)
    destination_ip = Column(String(45))
    destination_port = Column(Integer)
    protocol = Column(String(20))
    threat_level = Column(SQLEnum(ThreatLevel), nullable=False)
    threat_category = Column(SQLEnum(ThreatCategory), nullable=False)
    confidence_score = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    description = Column(Text)
    raw_payload = Column(JSON)
    ml_features = Column(JSON)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(255))
    resolved_at = Column(DateTime(timezone=True))
    auto_blocked = Column(Boolean, default=False)
    false_positive = Column(Boolean, default=False)
    mitre_technique = Column(String(50))
    mitre_tactic = Column(String(100))
    cve_references = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source_ip_ref = relationship("MonitoredIP", back_populates="threats")

    __table_args__ = (
        Index("ix_threat_events_source_ip", "source_ip"),
        Index("ix_threat_events_created_at", "created_at"),
        Index("ix_threat_events_level", "threat_level"),
    )


class NetworkFlow(Base):
    __tablename__ = "network_flows"

    id = Column(String, primary_key=True, default=generate_uuid)
    source_ip = Column(String(45), nullable=False)
    destination_ip = Column(String(45), nullable=False)
    source_port = Column(Integer)
    destination_port = Column(Integer)
    protocol = Column(String(20))
    bytes_sent = Column(Integer, default=0)
    bytes_received = Column(Integer, default=0)
    packets_sent = Column(Integer, default=0)
    packets_received = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    flags = Column(String(50))
    application = Column(String(100))
    risk_score = Column(Float, default=0.0)
    is_encrypted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_network_flows_source_ip", "source_ip"),
        Index("ix_network_flows_created_at", "created_at"),
    )


class SecurityPolicy(Base):
    __tablename__ = "security_policies"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    action = Column(SQLEnum(PolicyAction), nullable=False)
    
    # Conditions
    source_ip_range = Column(String(255))
    destination_ip_range = Column(String(255))
    destination_ports = Column(JSON, default=list)
    protocols = Column(JSON, default=list)
    countries = Column(JSON, default=list)
    time_range_start = Column(String(5))  # HH:MM
    time_range_end = Column(String(5))
    
    # Advanced conditions
    threat_level_min = Column(SQLEnum(ThreatLevel))
    risk_score_min = Column(Float)
    conditions = Column(JSON, default=dict)
    
    # Stats
    times_triggered = Column(Integer, default=0)
    last_triggered = Column(DateTime(timezone=True))
    
    created_by = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    severity = Column(SQLEnum(ThreatLevel), nullable=False)
    
    # Trigger conditions
    metric = Column(String(100))
    operator = Column(String(20))
    threshold = Column(Float)
    window_seconds = Column(Integer, default=60)
    
    # Notification
    notify_email = Column(JSON, default=list)
    notify_webhook = Column(String(255))
    
    times_triggered = Column(Integer, default=0)
    last_triggered = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id = Column(String, primary_key=True, default=generate_uuid)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    tags = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_system_metrics_name_time", "metric_name", "created_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(255))
    details = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    status = Column(String(20), default="success")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

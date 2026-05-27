"""
Extreme IP Guard - Pydantic Schemas
Request/response models for the API layer.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
import ipaddress


class ThreatLevelEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    SAFE = "safe"


class IPStatusEnum(str, Enum):
    BLOCKED = "blocked"
    WHITELISTED = "whitelisted"
    MONITORED = "monitored"
    QUARANTINED = "quarantined"
    UNKNOWN = "unknown"


class ActionTypeEnum(str, Enum):
    BLOCK = "block"
    ALLOW = "allow"
    RATE_LIMIT = "rate_limit"
    QUARANTINE = "quarantine"
    ALERT = "alert"
    LOG = "log"
    CHALLENGE = "challenge"
    REDIRECT = "redirect"


class IPAddressCreate(BaseModel):
    ip: str
    status: Optional[IPStatusEnum] = IPStatusEnum.UNKNOWN
    tags: Optional[List[str]] = []

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, v):
        try:
            ipaddress.ip_address(v)
        except ValueError:
            try:
                ipaddress.ip_network(v, strict=False)
            except ValueError:
                raise ValueError(f"Invalid IP address or network: {v}")
        return v


class IPAddressResponse(BaseModel):
    id: int
    ip: str
    version: int
    status: IPStatusEnum
    threat_score: float
    reputation_score: float
    country: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    asn: Optional[str] = None
    org: Optional[str] = None
    isp: Optional[str] = None
    is_vpn: bool
    is_tor: bool
    is_proxy: bool
    is_bot: bool
    is_datacenter: bool
    total_requests: int
    blocked_requests: int
    first_seen: datetime
    last_seen: datetime
    tags: List[str]

    class Config:
        from_attributes = True


class IPAnalysisResult(BaseModel):
    ip: str
    threat_score: float
    reputation_score: float
    threat_level: ThreatLevelEnum
    risk_factors: List[str]
    geo_info: dict
    network_info: dict
    behavioral_analysis: dict
    recommendations: List[str]
    analyzed_at: datetime


class ThreatEventResponse(BaseModel):
    id: int
    ip_id: int
    event_type: str
    threat_level: ThreatLevelEnum
    description: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    action_taken: Optional[ActionTypeEnum] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class SecurityRuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    enabled: bool = True
    priority: int = Field(default=100, ge=1, le=10000)
    rule_type: str
    conditions: dict
    action: ActionTypeEnum
    action_params: Optional[dict] = {}


class SecurityRuleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    enabled: bool
    priority: int
    rule_type: str
    conditions: dict
    action: ActionTypeEnum
    action_params: dict
    hit_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_ips_tracked: int
    active_threats: int
    blocked_ips: int
    whitelisted_ips: int
    quarantined_ips: int
    events_last_24h: int
    events_last_hour: int
    active_rules: int
    avg_threat_score: float
    top_threat_countries: List[dict]
    threat_level_distribution: dict
    recent_events: List[ThreatEventResponse]
    system_health: dict


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class BulkIPAction(BaseModel):
    ips: List[str]
    action: ActionTypeEnum

    @field_validator("ips")
    @classmethod
    def validate_ips(cls, v):
        for ip in v:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise ValueError(f"Invalid IP address: {ip}")
        return v


class TrafficSnapshot(BaseModel):
    timestamp: datetime
    requests_per_second: float
    unique_ips: int
    blocked_count: int
    threat_events: int
    bandwidth_mbps: float
    top_ips: List[dict]
    geo_distribution: dict


class AlertConfig(BaseModel):
    threat_score_threshold: float = Field(default=70.0, ge=0.0, le=100.0)
    auto_block_threshold: float = Field(default=90.0, ge=0.0, le=100.0)
    rate_limit_max: int = Field(default=100, ge=1)
    ddos_threshold: int = Field(default=1000, ge=10)
    port_scan_threshold: int = Field(default=15, ge=1)
    brute_force_threshold: int = Field(default=10, ge=1)

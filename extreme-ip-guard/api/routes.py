"""
Extreme IP Guard - API Routes
REST API endpoints for IP management, threat analysis, and system control.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import create_access_token, get_current_user
from core.database import get_db
from core.models import (
    IPAddress, ThreatEvent, SecurityRule as SecurityRuleModel,
    AuditLog, ThreatLevel, IPStatus, ActionType, EventType
)
from core.schemas import (
    IPAddressCreate, IPAddressResponse, IPAnalysisResult,
    ThreatEventResponse, SecurityRuleCreate, SecurityRuleResponse,
    DashboardStats, LoginRequest, TokenResponse, BulkIPAction,
    AlertConfig,
)
from core.threat_engine import threat_engine
from modules.rate_limiter import rate_limiter
from modules.ddos_detector import ddos_detector
from modules.port_scan_detector import port_scan_detector
from modules.brute_force_detector import brute_force_detector
from modules.anomaly_detector import anomaly_detector
from modules.rules_engine import rules_engine
from modules.geo_intelligence import geo_intelligence
from config.settings import settings

router = APIRouter()


# ── Authentication ──────────────────────────────────────────────

@router.post("/auth/login", response_model=TokenResponse, tags=["Authentication"])
async def login(request: LoginRequest):
    if (
        request.username == settings.ADMIN_USERNAME
        and request.password == settings.ADMIN_PASSWORD
    ):
        token = create_access_token(
            data={"sub": request.username, "role": "admin"}
        )
        return TokenResponse(
            access_token=token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )


# ── Dashboard ───────────────────────────────────────────────────

@router.get("/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    h24 = now - timedelta(hours=24)
    h1 = now - timedelta(hours=1)

    total = await db.scalar(select(func.count(IPAddress.id)))
    blocked = await db.scalar(
        select(func.count(IPAddress.id)).where(IPAddress.status == IPStatus.BLOCKED)
    )
    whitelisted = await db.scalar(
        select(func.count(IPAddress.id)).where(IPAddress.status == IPStatus.WHITELISTED)
    )
    quarantined = await db.scalar(
        select(func.count(IPAddress.id)).where(IPAddress.status == IPStatus.QUARANTINED)
    )
    active_threats = await db.scalar(
        select(func.count(IPAddress.id)).where(
            IPAddress.threat_score >= settings.THREAT_SCORE_THRESHOLD
        )
    )

    events_24h = await db.scalar(
        select(func.count(ThreatEvent.id)).where(ThreatEvent.timestamp >= h24)
    )
    events_1h = await db.scalar(
        select(func.count(ThreatEvent.id)).where(ThreatEvent.timestamp >= h1)
    )

    active_rules = await db.scalar(
        select(func.count(SecurityRuleModel.id)).where(SecurityRuleModel.enabled == True)
    )

    avg_threat = await db.scalar(select(func.avg(IPAddress.threat_score)))

    country_result = await db.execute(
        select(IPAddress.country, func.count(IPAddress.id))
        .where(and_(
            IPAddress.threat_score >= settings.THREAT_SCORE_THRESHOLD,
            IPAddress.country.isnot(None),
        ))
        .group_by(IPAddress.country)
        .order_by(desc(func.count(IPAddress.id)))
        .limit(10)
    )
    top_countries = [
        {"country": row[0], "count": row[1]}
        for row in country_result.all()
    ]

    level_result = await db.execute(
        select(ThreatEvent.threat_level, func.count(ThreatEvent.id))
        .where(ThreatEvent.timestamp >= h24)
        .group_by(ThreatEvent.threat_level)
    )
    threat_distribution = {
        str(row[0].value if hasattr(row[0], "value") else row[0]): row[1]
        for row in level_result.all()
    }

    recent_result = await db.execute(
        select(ThreatEvent)
        .order_by(desc(ThreatEvent.timestamp))
        .limit(20)
    )
    recent_events = recent_result.scalars().all()

    return {
        "total_ips_tracked": total or 0,
        "active_threats": active_threats or 0,
        "blocked_ips": blocked or 0,
        "whitelisted_ips": whitelisted or 0,
        "quarantined_ips": quarantined or 0,
        "events_last_24h": events_24h or 0,
        "events_last_hour": events_1h or 0,
        "active_rules": active_rules or 0,
        "avg_threat_score": round(avg_threat or 0, 2),
        "top_threat_countries": top_countries,
        "threat_level_distribution": threat_distribution,
        "recent_events": [
            {
                "id": e.id,
                "ip_id": e.ip_id,
                "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
                "threat_level": e.threat_level.value if hasattr(e.threat_level, "value") else str(e.threat_level),
                "description": e.description,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in recent_events
        ],
        "system_health": {
            "rate_limiter": rate_limiter.get_stats(),
            "ddos_detector": ddos_detector.get_status(),
            "port_scan_detector": port_scan_detector.get_stats(),
            "brute_force_detector": brute_force_detector.get_stats(),
            "anomaly_detector": anomaly_detector.get_stats(),
            "rules_engine": rules_engine.get_stats(),
        },
    }


# ── IP Management ───────────────────────────────────────────────

@router.get("/ips", tags=["IP Management"])
async def list_ips(
    status: Optional[str] = None,
    min_threat: Optional[float] = None,
    country: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort_by: str = "threat_score",
    sort_dir: str = "desc",
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    query = select(IPAddress)

    if status:
        query = query.where(IPAddress.status == IPStatus(status))
    if min_threat is not None:
        query = query.where(IPAddress.threat_score >= min_threat)
    if country:
        query = query.where(IPAddress.country == country)
    if search:
        query = query.where(IPAddress.ip.contains(search))

    sort_column = getattr(IPAddress, sort_by, IPAddress.threat_score)
    if sort_dir == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    total = await db.scalar(
        select(func.count()).select_from(query.subquery())
    )

    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    ips = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total else 0,
        "items": [
            {
                "id": ip.id,
                "ip": ip.ip,
                "version": ip.version,
                "status": ip.status.value if hasattr(ip.status, "value") else str(ip.status),
                "threat_score": ip.threat_score,
                "reputation_score": ip.reputation_score,
                "country": ip.country,
                "city": ip.city,
                "asn": ip.asn,
                "org": ip.org,
                "is_vpn": ip.is_vpn,
                "is_tor": ip.is_tor,
                "is_proxy": ip.is_proxy,
                "is_bot": ip.is_bot,
                "total_requests": ip.total_requests,
                "blocked_requests": ip.blocked_requests,
                "first_seen": ip.first_seen.isoformat() if ip.first_seen else None,
                "last_seen": ip.last_seen.isoformat() if ip.last_seen else None,
                "tags": ip.tags or [],
            }
            for ip in ips
        ],
    }


@router.post("/ips", tags=["IP Management"])
async def add_ip(
    data: IPAddressCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    existing = await db.execute(
        select(IPAddress).where(IPAddress.ip == data.ip)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="IP already exists")

    ip_record = IPAddress(
        ip=data.ip,
        version=4 if "." in data.ip else 6,
        status=IPStatus(data.status.value),
        tags=data.tags,
    )
    db.add(ip_record)
    await db.commit()
    await db.refresh(ip_record)
    return {"message": "IP added successfully", "id": ip_record.id}


@router.get("/ips/{ip_address}/analyze", tags=["IP Management"])
async def analyze_ip(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    analysis = await threat_engine.analyze_ip(ip_address, db)
    geo = geo_intelligence.lookup(ip_address)
    analysis["geo_info"] = geo
    return analysis


@router.post("/ips/{ip_address}/block", tags=["IP Management"])
async def block_ip(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(IPAddress).where(IPAddress.ip == ip_address)
    )
    ip_record = result.scalar_one_or_none()
    if not ip_record:
        ip_record = IPAddress(ip=ip_address, version=4 if "." in ip_address else 6)
        db.add(ip_record)
        await db.flush()

    ip_record.status = IPStatus.BLOCKED
    audit = AuditLog(
        actor=_user.get("sub", "system"),
        action="block_ip",
        target_type="ip",
        target_id=ip_address,
        details={"reason": "manual_block"},
    )
    db.add(audit)
    await db.commit()
    return {"message": f"IP {ip_address} blocked", "status": "blocked"}


@router.post("/ips/{ip_address}/unblock", tags=["IP Management"])
async def unblock_ip(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(IPAddress).where(IPAddress.ip == ip_address)
    )
    ip_record = result.scalar_one_or_none()
    if not ip_record:
        raise HTTPException(status_code=404, detail="IP not found")

    ip_record.status = IPStatus.UNKNOWN
    audit = AuditLog(
        actor=_user.get("sub", "system"),
        action="unblock_ip",
        target_type="ip",
        target_id=ip_address,
    )
    db.add(audit)
    await db.commit()
    return {"message": f"IP {ip_address} unblocked"}


@router.post("/ips/{ip_address}/whitelist", tags=["IP Management"])
async def whitelist_ip(
    ip_address: str,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(IPAddress).where(IPAddress.ip == ip_address)
    )
    ip_record = result.scalar_one_or_none()
    if not ip_record:
        ip_record = IPAddress(ip=ip_address, version=4 if "." in ip_address else 6)
        db.add(ip_record)
        await db.flush()

    ip_record.status = IPStatus.WHITELISTED
    ip_record.threat_score = 0.0
    ip_record.reputation_score = 100.0
    await db.commit()
    return {"message": f"IP {ip_address} whitelisted"}


@router.post("/ips/bulk-action", tags=["IP Management"])
async def bulk_ip_action(
    data: BulkIPAction,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    results = []
    status_map = {
        "block": IPStatus.BLOCKED,
        "allow": IPStatus.WHITELISTED,
        "quarantine": IPStatus.QUARANTINED,
    }

    new_status = status_map.get(data.action.value)
    for ip_str in data.ips:
        result = await db.execute(
            select(IPAddress).where(IPAddress.ip == ip_str)
        )
        ip_record = result.scalar_one_or_none()
        if not ip_record:
            ip_record = IPAddress(ip=ip_str, version=4 if "." in ip_str else 6)
            db.add(ip_record)
            await db.flush()

        if new_status:
            ip_record.status = new_status
        results.append({"ip": ip_str, "action": data.action.value, "success": True})

    await db.commit()
    return {"results": results, "total_processed": len(results)}


# ── Threat Events ───────────────────────────────────────────────

@router.get("/events", tags=["Threat Events"])
async def list_events(
    event_type: Optional[str] = None,
    threat_level: Optional[str] = None,
    ip_id: Optional[int] = None,
    hours: int = Query(24, ge=1, le=720),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    query = select(ThreatEvent).where(ThreatEvent.timestamp >= since)

    if event_type:
        query = query.where(ThreatEvent.event_type == EventType(event_type))
    if threat_level:
        query = query.where(ThreatEvent.threat_level == ThreatLevel(threat_level))
    if ip_id:
        query = query.where(ThreatEvent.ip_id == ip_id)

    query = query.order_by(desc(ThreatEvent.timestamp))
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page))
    events = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "items": [
            {
                "id": e.id,
                "ip_id": e.ip_id,
                "event_type": e.event_type.value if hasattr(e.event_type, "value") else str(e.event_type),
                "threat_level": e.threat_level.value if hasattr(e.threat_level, "value") else str(e.threat_level),
                "description": e.description,
                "source_port": e.source_port,
                "destination_port": e.destination_port,
                "protocol": e.protocol,
                "action_taken": e.action_taken.value if e.action_taken and hasattr(e.action_taken, "value") else str(e.action_taken) if e.action_taken else None,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            }
            for e in events
        ],
    }


@router.post("/events/simulate", tags=["Threat Events"])
async def simulate_event(
    ip: str,
    event_type: str,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Simulate a threat event for testing."""
    result = await threat_engine.process_event(
        ip_str=ip,
        event_type=EventType(event_type),
        db=db,
        description=description or f"Simulated {event_type} event",
    )
    return result


# ── Security Rules ──────────────────────────────────────────────

@router.get("/rules", tags=["Security Rules"])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(SecurityRuleModel).order_by(SecurityRuleModel.priority)
    )
    rules = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "enabled": r.enabled,
            "priority": r.priority,
            "rule_type": r.rule_type,
            "conditions": r.conditions,
            "action": r.action.value if hasattr(r.action, "value") else str(r.action),
            "action_params": r.action_params,
            "hit_count": r.hit_count,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rules
    ]


@router.post("/rules", tags=["Security Rules"])
async def create_rule(
    data: SecurityRuleCreate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    rule = SecurityRuleModel(
        name=data.name,
        description=data.description,
        enabled=data.enabled,
        priority=data.priority,
        rule_type=data.rule_type,
        conditions=data.conditions,
        action=ActionType(data.action.value),
        action_params=data.action_params,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return {"message": "Rule created", "id": rule.id}


@router.delete("/rules/{rule_id}", tags=["Security Rules"])
async def delete_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(SecurityRuleModel).where(SecurityRuleModel.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    await db.delete(rule)
    await db.commit()
    return {"message": "Rule deleted"}


# ── Security Modules Status ─────────────────────────────────────

@router.get("/security/ddos", tags=["Security Modules"])
async def get_ddos_status(
    _user: dict = Depends(get_current_user),
):
    return await ddos_detector.analyze()


@router.get("/security/rate-limiter", tags=["Security Modules"])
async def get_rate_limiter_status(
    _user: dict = Depends(get_current_user),
):
    return rate_limiter.get_stats()


@router.get("/security/port-scans", tags=["Security Modules"])
async def get_port_scan_status(
    _user: dict = Depends(get_current_user),
):
    return {
        "stats": port_scan_detector.get_stats(),
        "active_scans": port_scan_detector.get_active_scans(),
        "recent_detections": port_scan_detector.get_recent_detections(20),
    }


@router.get("/security/brute-force", tags=["Security Modules"])
async def get_brute_force_status(
    _user: dict = Depends(get_current_user),
):
    return {
        "stats": brute_force_detector.get_stats(),
        "locked_ips": brute_force_detector.get_locked_ips(),
        "recent_detections": brute_force_detector.get_recent_detections(20),
        "spraying_alerts": brute_force_detector.check_password_spraying(),
    }


@router.get("/security/anomalies", tags=["Security Modules"])
async def get_anomaly_status(
    _user: dict = Depends(get_current_user),
):
    return {
        "stats": anomaly_detector.get_stats(),
        "recent_anomalies": anomaly_detector.get_recent_anomalies(20),
    }


@router.get("/security/geo", tags=["Security Modules"])
async def get_geo_status(
    _user: dict = Depends(get_current_user),
):
    return geo_intelligence.get_country_stats()


@router.get("/security/geo/{ip_address}", tags=["Security Modules"])
async def lookup_geo(
    ip_address: str,
    _user: dict = Depends(get_current_user),
):
    return geo_intelligence.lookup(ip_address)


# ── Audit Logs ──────────────────────────────────────────────────

@router.get("/audit", tags=["Audit"])
async def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    total = await db.scalar(select(func.count(AuditLog.id)))
    offset = (page - 1) * per_page
    result = await db.execute(
        select(AuditLog)
        .order_by(desc(AuditLog.timestamp))
        .offset(offset)
        .limit(per_page)
    )
    logs = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "items": [
            {
                "id": l.id,
                "actor": l.actor,
                "action": l.action,
                "target_type": l.target_type,
                "target_id": l.target_id,
                "details": l.details,
                "timestamp": l.timestamp.isoformat() if l.timestamp else None,
            }
            for l in logs
        ],
    }

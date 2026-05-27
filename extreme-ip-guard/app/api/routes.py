"""
Extreme IP Guard - API Routes
RESTful API endpoints for the security platform.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel, Field

from app.models.database import get_db
from app.models.schemas import IPStatus, ThreatLevel, AlertType, RuleAction
from app.services.ip_service import IPService
from app.core.threat_engine import threat_engine
from app.core.ip_intelligence import ip_intel_service
from app.core.network_monitor import network_monitor

router = APIRouter(prefix="/api/v1", tags=["Extreme IP Guard API"])


class IPAddRequest(BaseModel):
    ip_address: str = Field(..., description="IP address to monitor")
    notes: Optional[str] = Field(None, description="Optional notes")


class IPAnalyzeRequest(BaseModel):
    ip_address: str
    dest_port: int = 80
    method: str = "GET"
    path: str = "/"
    user_agent: str = ""


class FirewallRuleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    source_ip: Optional[str] = None
    source_cidr: Optional[str] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    action: RuleAction = RuleAction.BLOCK
    priority: int = 100


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    stats = await service.get_dashboard_stats()
    system = network_monitor.get_system_stats()
    bandwidth = network_monitor.get_bandwidth_history()
    anomalies = network_monitor.detect_anomalies()

    return {
        "status": "operational",
        "stats": stats,
        "system": system,
        "bandwidth": bandwidth,
        "anomalies": anomalies,
    }


@router.get("/ips")
async def list_ips(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    service = IPService(db)
    ips = await service.get_all_ips(limit=limit, offset=offset, status=status)
    return {
        "ips": [
            {
                "id": ip.id,
                "ip_address": ip.ip_address,
                "hostname": ip.hostname,
                "status": ip.status.value if ip.status else "monitoring",
                "threat_level": ip.threat_level.value if ip.threat_level else "safe",
                "threat_score": ip.threat_score,
                "reputation_score": ip.reputation_score,
                "country": ip.country,
                "country_code": ip.country_code,
                "city": ip.city,
                "latitude": ip.latitude,
                "longitude": ip.longitude,
                "asn": ip.asn,
                "org": ip.org,
                "isp": ip.isp,
                "is_vpn": ip.is_vpn,
                "is_proxy": ip.is_proxy,
                "is_tor": ip.is_tor,
                "is_bot": ip.is_bot,
                "total_requests": ip.total_requests,
                "blocked_requests": ip.blocked_requests,
                "first_seen": ip.first_seen.isoformat() if ip.first_seen else None,
                "last_seen": ip.last_seen.isoformat() if ip.last_seen else None,
                "notes": ip.notes,
            }
            for ip in ips
        ],
        "total": len(ips),
    }


@router.post("/ips")
async def add_ip(request: IPAddRequest, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    ip_record = await service.add_ip(request.ip_address, request.notes)
    return {"status": "success", "ip_id": ip_record.id, "ip_address": ip_record.ip_address}


@router.post("/ips/{ip_id}/block")
async def block_ip(ip_id: int, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    result = await service.block_ip(ip_id)
    if not result:
        raise HTTPException(status_code=404, detail="IP not found")
    return {"status": "blocked", "ip_address": result.ip_address}


@router.post("/ips/{ip_id}/unblock")
async def unblock_ip(ip_id: int, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    result = await service.unblock_ip(ip_id)
    if not result:
        raise HTTPException(status_code=404, detail="IP not found")
    return {"status": "unblocked", "ip_address": result.ip_address}


@router.post("/ips/{ip_id}/whitelist")
async def whitelist_ip(ip_id: int, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    result = await service.whitelist_ip(ip_id)
    if not result:
        raise HTTPException(status_code=404, detail="IP not found")
    return {"status": "whitelisted", "ip_address": result.ip_address}


@router.delete("/ips/{ip_id}")
async def delete_ip(ip_id: int, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    success = await service.delete_ip(ip_id)
    if not success:
        raise HTTPException(status_code=404, detail="IP not found")
    return {"status": "deleted"}


@router.post("/analyze")
async def analyze_ip(request: IPAnalyzeRequest):
    threat_result = await threat_engine.analyze_request(
        source_ip=request.ip_address,
        dest_port=request.dest_port,
        method=request.method,
        path=request.path,
        user_agent=request.user_agent,
    )
    intel = await ip_intel_service.analyze(request.ip_address)

    return {
        "ip": request.ip_address,
        "threat_analysis": threat_result,
        "intelligence": {
            "hostname": intel.hostname,
            "country": intel.country,
            "country_code": intel.country_code,
            "city": intel.city,
            "region": intel.region,
            "latitude": intel.latitude,
            "longitude": intel.longitude,
            "asn": intel.asn,
            "org": intel.org,
            "isp": intel.isp,
            "is_vpn": intel.is_vpn,
            "is_proxy": intel.is_proxy,
            "is_tor": intel.is_tor,
            "is_datacenter": intel.is_datacenter,
            "risk_score": intel.risk_score,
            "abuse_confidence": intel.abuse_confidence,
            "ip_version": intel.ip_version,
            "network_class": intel.network_class,
        },
    }


@router.get("/intel/{ip_address}")
async def get_ip_intelligence(ip_address: str):
    intel = await ip_intel_service.analyze(ip_address)
    return {
        "ip": ip_address,
        "hostname": intel.hostname,
        "reverse_dns": intel.reverse_dns,
        "country": intel.country,
        "country_code": intel.country_code,
        "city": intel.city,
        "region": intel.region,
        "coordinates": {"lat": intel.latitude, "lng": intel.longitude},
        "network": {
            "asn": intel.asn,
            "org": intel.org,
            "isp": intel.isp,
            "ip_version": intel.ip_version,
            "network_class": intel.network_class,
            "is_private": intel.is_private,
            "is_loopback": intel.is_loopback,
        },
        "anonymizer": {
            "is_vpn": intel.is_vpn,
            "is_proxy": intel.is_proxy,
            "is_tor": intel.is_tor,
            "is_datacenter": intel.is_datacenter,
        },
        "risk": {
            "risk_score": intel.risk_score,
            "abuse_confidence": intel.abuse_confidence,
        },
    }


@router.get("/alerts")
async def list_alerts(
    limit: int = Query(50, ge=1, le=500),
    unresolved_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    service = IPService(db)
    alerts = await service.get_alerts(limit=limit, unresolved_only=unresolved_only)
    return {
        "alerts": [
            {
                "id": a.id,
                "alert_type": a.alert_type.value if a.alert_type else "",
                "threat_level": a.threat_level.value if a.threat_level else "",
                "title": a.title,
                "description": a.description,
                "source_ip": a.source_ip,
                "is_resolved": a.is_resolved,
                "resolved_by": a.resolved_by,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            }
            for a in alerts
        ],
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    alert = await service.resolve_alert(alert_id, resolved_by="admin")
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "resolved", "alert_id": alert.id}


@router.get("/firewall/rules")
async def list_firewall_rules(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    service = IPService(db)
    rules = await service.get_firewall_rules(active_only=active_only)
    return {
        "rules": [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "source_ip": r.source_ip,
                "source_cidr": r.source_cidr,
                "destination_port": r.destination_port,
                "protocol": r.protocol,
                "action": r.action.value if r.action else "block",
                "priority": r.priority,
                "is_active": r.is_active,
                "hit_count": r.hit_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rules
        ],
    }


@router.post("/firewall/rules")
async def create_firewall_rule(request: FirewallRuleRequest, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    rule = await service.create_firewall_rule(
        name=request.name,
        description=request.description,
        source_ip=request.source_ip,
        source_cidr=request.source_cidr,
        destination_port=request.destination_port,
        protocol=request.protocol,
        action=request.action,
        priority=request.priority,
    )
    return {"status": "created", "rule_id": rule.id}


@router.post("/firewall/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    rule = await service.toggle_firewall_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "toggled", "is_active": rule.is_active}


@router.delete("/firewall/rules/{rule_id}")
async def delete_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    success = await service.delete_firewall_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "deleted"}


@router.get("/network/stats")
async def network_stats():
    snapshot = await network_monitor.capture_snapshot()
    connections = network_monitor.get_active_connections()
    system = network_monitor.get_system_stats()
    anomalies = network_monitor.detect_anomalies()

    return {
        "snapshot": {
            "bytes_sent": snapshot.bytes_sent,
            "bytes_recv": snapshot.bytes_recv,
            "packets_sent": snapshot.packets_sent,
            "packets_recv": snapshot.packets_recv,
            "connections_active": snapshot.connections_active,
            "connections_established": snapshot.connections_established,
            "bandwidth_in_mbps": snapshot.bandwidth_in_mbps,
            "bandwidth_out_mbps": snapshot.bandwidth_out_mbps,
            "cpu_percent": snapshot.cpu_percent,
            "memory_percent": snapshot.memory_percent,
        },
        "active_connections": [
            {
                "local": f"{c.local_addr}:{c.local_port}",
                "remote": f"{c.remote_addr}:{c.remote_port}",
                "status": c.status,
                "process": c.process_name,
            }
            for c in connections[:50]
        ],
        "system": system,
        "anomalies": anomalies,
    }


@router.get("/network/bandwidth")
async def bandwidth_history(points: int = Query(60, ge=10, le=300)):
    return network_monitor.get_bandwidth_history(points)


@router.get("/events")
async def list_events(limit: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)):
    service = IPService(db)
    events = await service.get_system_events(limit=limit)
    return {
        "events": [
            {
                "id": e.id,
                "type": e.event_type,
                "severity": e.severity.value if e.severity else "info",
                "message": e.message,
                "details": e.details,
                "source": e.source,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ],
    }


@router.get("/engine/stats")
async def engine_stats():
    return threat_engine.get_stats()

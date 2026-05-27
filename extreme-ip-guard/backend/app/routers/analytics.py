from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.services.analytics_service import get_analytics_service
from app.routers.auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/threat-timeline")
async def get_threat_timeline(
    hours: int = Query(24, ge=1, le=168),
    current_user: dict = Depends(get_current_user)
):
    service = get_analytics_service()
    return {"timeline": service.get_threat_timeline(hours)}


@router.get("/geo-distribution")
async def get_geo_distribution(current_user: dict = Depends(get_current_user)):
    service = get_analytics_service()
    return {"distribution": service.get_geo_distribution()}


@router.get("/attack-categories")
async def get_attack_categories(current_user: dict = Depends(get_current_user)):
    service = get_analytics_service()
    return {"categories": service.get_attack_categories()}


@router.get("/top-threats")
async def get_top_threats(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    service = get_analytics_service()
    return {"threats": service.get_top_threats(limit)}


@router.get("/network-topology")
async def get_network_topology(current_user: dict = Depends(get_current_user)):
    service = get_analytics_service()
    return service.get_network_topology()


@router.get("/performance")
async def get_performance_metrics(current_user: dict = Depends(get_current_user)):
    service = get_analytics_service()
    return service.get_performance_metrics()


@router.get("/summary")
async def get_summary(current_user: dict = Depends(get_current_user)):
    service = get_analytics_service()
    return service.get_summary_stats()

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import List, Optional
from app.services.monitor_service import get_monitoring_service, get_connection_manager
from app.routers.auth import get_current_user
from loguru import logger

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    cm = get_connection_manager()
    client_id = f"client-{id(websocket)}"
    
    await cm.connect(websocket, client_id)
    
    try:
        # Send initial state
        service = get_monitoring_service()
        await cm.send_personal({
            "type": "connected",
            "message": "Connected to Extreme IP Guard monitoring stream",
            "stats": service.get_dashboard_stats(),
        }, websocket)
        
        while True:
            # Keep connection alive, handle ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await cm.send_personal({"type": "pong"}, websocket)
    except WebSocketDisconnect:
        cm.disconnect(websocket)
        logger.info(f"WebSocket client disconnected: {client_id}")
    except Exception as e:
        cm.disconnect(websocket)
        logger.error(f"WebSocket error for {client_id}: {e}")


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    service = get_monitoring_service()
    return service.get_dashboard_stats()


@router.get("/events")
async def get_recent_events(
    limit: int = Query(100, le=500),
    current_user: dict = Depends(get_current_user)
):
    service = get_monitoring_service()
    return {
        "events": service.get_recent_events(limit),
        "total": len(service.recent_events),
    }


@router.get("/threats")
async def get_recent_threats(
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user)
):
    service = get_monitoring_service()
    return {
        "threats": service.get_recent_threats(limit),
        "total": len(service.recent_threats),
    }


@router.post("/start")
async def start_monitoring(current_user: dict = Depends(get_current_user)):
    service = get_monitoring_service()
    await service.start()
    return {"status": "started", "message": "Network monitoring activated"}


@router.post("/stop")
async def stop_monitoring(current_user: dict = Depends(get_current_user)):
    service = get_monitoring_service()
    await service.stop()
    return {"status": "stopped", "message": "Network monitoring paused"}


@router.get("/blocked-ips")
async def get_blocked_ips(current_user: dict = Depends(get_current_user)):
    service = get_monitoring_service()
    return {"blocked_ips": service.get_blocked_ips()}


@router.post("/block-ip/{ip}")
async def block_ip(ip: str, current_user: dict = Depends(get_current_user)):
    service = get_monitoring_service()
    success = service.block_ip(ip)
    return {"success": success, "ip": ip, "action": "blocked"}


@router.delete("/block-ip/{ip}")
async def unblock_ip(ip: str, current_user: dict = Depends(get_current_user)):
    service = get_monitoring_service()
    success = service.unblock_ip(ip)
    return {"success": success, "ip": ip, "action": "unblocked"}

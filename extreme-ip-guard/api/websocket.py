"""
Extreme IP Guard - WebSocket Real-Time Feed
Pushes live threat events, system metrics, and alerts
to connected dashboard clients.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Set

from fastapi import WebSocket, WebSocketDisconnect

from config.settings import settings


class ConnectionManager:
    """Manages WebSocket connections with heartbeat and broadcast."""

    def __init__(self):
        self._connections: Dict[str, WebSocket] = {}
        self._subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self._connections[client_id] = websocket
        self._subscriptions[client_id] = {"all"}
        await self._send_to(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Connected to Extreme IP Guard real-time feed",
        })

    def disconnect(self, client_id: str):
        self._connections.pop(client_id, None)
        self._subscriptions.pop(client_id, None)

    async def subscribe(self, client_id: str, channels: Set[str]):
        if client_id in self._subscriptions:
            self._subscriptions[client_id].update(channels)

    async def broadcast(self, message: dict, channel: str = "all"):
        disconnected = []
        for client_id, ws in self._connections.items():
            subs = self._subscriptions.get(client_id, set())
            if "all" in subs or channel in subs:
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(client_id)

        for cid in disconnected:
            self.disconnect(cid)

    async def _send_to(self, client_id: str, message: dict):
        ws = self._connections.get(client_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(client_id)

    async def broadcast_threat_event(self, event_data: dict):
        await self.broadcast(
            {"type": "threat_event", "data": event_data, "timestamp": datetime.now(timezone.utc).isoformat()},
            channel="threats",
        )

    async def broadcast_metrics(self, metrics: dict):
        await self.broadcast(
            {"type": "metrics", "data": metrics, "timestamp": datetime.now(timezone.utc).isoformat()},
            channel="metrics",
        )

    async def broadcast_alert(self, alert: dict):
        await self.broadcast(
            {"type": "alert", "data": alert, "timestamp": datetime.now(timezone.utc).isoformat()},
            channel="alerts",
        )

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    def get_status(self) -> dict:
        return {
            "active_connections": self.active_connections,
            "clients": list(self._connections.keys()),
        }


ws_manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket):
    client_id = f"client_{id(websocket)}_{int(time.time())}"
    await ws_manager.connect(websocket, client_id)

    try:
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.WEBSOCKET_HEARTBEAT,
                )
                msg = json.loads(data)

                if msg.get("type") == "subscribe":
                    channels = set(msg.get("channels", []))
                    await ws_manager.subscribe(client_id, channels)
                    await ws_manager._send_to(client_id, {
                        "type": "subscribed",
                        "channels": list(channels),
                    })
                elif msg.get("type") == "ping":
                    await ws_manager._send_to(client_id, {"type": "pong"})

            except asyncio.TimeoutError:
                await ws_manager._send_to(client_id, {
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
    except Exception:
        ws_manager.disconnect(client_id)

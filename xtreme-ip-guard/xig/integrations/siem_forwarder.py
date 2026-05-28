# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Forward Mersal alerts and events to enterprise SIEM (syslog/CEF) — standalone export."""

from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database

_CURSOR_KEY = "siem_forward_cursor"


class SiemForwarder:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def forward_batch(self, *, limit: int = 100) -> dict[str, Any]:
        forwarders = self.db.list_siem_forwarders(enabled_only=True)
        if not forwarders:
            return {"forwarded": 0, "forwarders": 0, "skipped": True}
        cursor = self._load_cursor()
        alerts = self._alerts_after_cursor(cursor, limit=limit)
        events = self._events_after_cursor(cursor, limit=min(20, limit))
        sent = 0
        deduped = 0
        seen: set[str] = set()
        for fw in forwarders:
            for alert in alerts:
                key = f"alert:{alert.get('alert_id')}"
                if key in seen:
                    deduped += 1
                    continue
                if self._send(fw, self._format_cef("siem_alert", alert)):
                    seen.add(key)
                    sent += 1
            for event in events:
                key = f"event:{event.get('event_id')}"
                if key in seen:
                    deduped += 1
                    continue
                if self._send(fw, self._format_cef("endpoint_event", event)):
                    seen.add(key)
                    sent += 1
        self._save_cursor(alerts, events)
        return {
            "forwarded": sent,
            "forwarders": len(forwarders),
            "deduped": deduped,
            "cursor": self._load_cursor(),
        }

    def _load_cursor(self) -> dict[str, Any]:
        raw = self.db.get_platform_setting(_CURSOR_KEY, "{}")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def _save_cursor(self, alerts: list[dict[str, Any]], events: list[dict[str, Any]]) -> None:
        cursor = self._load_cursor()
        if alerts:
            cursor["last_alert_id"] = max(int(a.get("alert_id", 0) or 0) for a in alerts)
        if events:
            cursor["last_event_id"] = max(int(e.get("event_id", 0) or 0) for e in events)
        self.db.set_platform_setting(_CURSOR_KEY, json.dumps(cursor, sort_keys=True))

    def _alerts_after_cursor(self, cursor: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
        last_id = int(cursor.get("last_alert_id", 0) or 0)
        alerts = self.db.list_siem_alerts(limit=limit * 2)
        fresh = [a for a in alerts if int(a.get("alert_id", 0) or 0) > last_id]
        return fresh[:limit]

    def _events_after_cursor(self, cursor: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
        last_id = int(cursor.get("last_event_id", 0) or 0)
        events = self.db.list_events(limit=limit * 3)
        fresh = [e for e in events if int(e.get("event_id", 0) or 0) > last_id]
        return fresh[:limit]

    def _format_cef(self, event_type: str, record: dict[str, Any]) -> str:
        ts = datetime.now(timezone.utc).strftime("%b %d %Y %H:%M:%S")
        name = str(record.get("title") or record.get("event_type") or event_type)
        severity = int(record.get("severity", record.get("risk_score", 5)))
        ext = "|".join(
            f"{k}={self._cef_escape(str(v))}"
            for k, v in {
                "endpointId": record.get("endpoint_id", ""),
                "ruleId": record.get("rule_id", ""),
                "action": record.get("action", ""),
            }.items()
            if v
        )
        return (
            f"CEF:0|Mersal|Ionomegax-Mersal|8.0|{event_type}|{name}|{severity}|"
            f"rt={ts} {ext}"
        )

    @staticmethod
    def _cef_escape(value: str) -> str:
        return value.replace("\\", "\\\\").replace("|", "\\|")

    def _send(self, forwarder: dict[str, Any], message: str) -> bool:
        host = str(forwarder["host"])
        port = int(forwarder["port"])
        proto = str(forwarder.get("protocol", "syslog_udp"))
        try:
            if proto == "syslog_udp":
                payload = message.encode("utf-8", errors="replace")
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.settimeout(3)
                    sock.sendto(payload, (host, port))
                return True
            if proto == "syslog_tcp":
                with socket.create_connection((host, port), timeout=5) as sock:
                    sock.sendall((message + "\n").encode("utf-8"))
                return True
        except OSError:
            return False
        return False

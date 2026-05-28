# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Forward Mersal alerts and events to enterprise SIEM (syslog/CEF) — standalone export."""

from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class SiemForwarder:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def forward_batch(self, *, limit: int = 100) -> dict[str, Any]:
        forwarders = self.db.list_siem_forwarders(enabled_only=True)
        if not forwarders:
            return {"forwarded": 0, "forwarders": 0, "skipped": True}
        alerts = self.db.list_siem_alerts(limit=limit)
        events = self.db.list_events(limit=limit)
        sent = 0
        for fw in forwarders:
            for alert in alerts:
                if self._send(fw, self._format_cef("siem_alert", alert)):
                    sent += 1
            for event in events[: min(20, len(events))]:
                if self._send(fw, self._format_cef("endpoint_event", event)):
                    sent += 1
        return {"forwarded": sent, "forwarders": len(forwarders)}

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

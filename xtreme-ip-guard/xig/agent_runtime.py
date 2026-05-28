# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Mersal Endpoint Agent — continuous heartbeat, sensors, and enforcement."""

from __future__ import annotations

import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import __version__
from .brand import BRAND
from .enforcement import LocalEnforcer
from .platform import collect_profile, collect_sensor_events
from .platform.vuln_probe import collect_vuln_probe


@dataclass
class AgentConfig:
    server: str
    agent_id: str
    endpoint_id: str
    owner: str
    site: str
    interval_seconds: int
    api_token: str
    state_dir: str

    @classmethod
    def load(cls, path: Path) -> "AgentConfig":
        payload = json.loads(path.read_text(encoding="utf-8"))
        hostname = socket.gethostname()
        endpoint_id = str(payload.get("endpoint_id") or hostname)
        return cls(
            server=str(payload.get("server", "http://127.0.0.1:8090")).rstrip("/"),
            agent_id=str(payload.get("agent_id") or f"mersal-agent-{endpoint_id}"),
            endpoint_id=endpoint_id,
            owner=str(payload.get("owner", "")),
            site=str(payload.get("site", "HQ")),
            interval_seconds=int(payload.get("interval_seconds", 30)),
            api_token=str(payload.get("api_token", os.environ.get("MERSAL_API_TOKEN", ""))),
            state_dir=str(payload.get("state_dir", str(Path.home() / ".mersal-guard"))),
        )


class MersalAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.enforcer = LocalEnforcer(Path(config.state_dir))
        self.profile = collect_profile()

    def run_forever(self) -> None:
        print(f"{BRAND['full_name']} agent {self.config.agent_id} on {self.profile.os_name}")
        while True:
            try:
                self.tick()
            except Exception as exc:  # noqa: BLE001 - agent must survive transient faults
                print(f"[mersal-agent] tick error: {exc}")
            time.sleep(max(5, self.config.interval_seconds))

    def tick(self) -> None:
        self.send_heartbeat()
        directives = self.fetch_directives()
        if directives.get("isolated"):
            self.enforcer.apply("isolate_endpoint", reason="Server marked endpoint isolated")
        for sensor in collect_sensor_events():
            if self.enforcer.should_block_channel(sensor.channel):
                print(f"[mersal-agent] blocked sensor channel {sensor.channel}: {sensor.resource}")
                continue
            result = self.send_event(sensor)
            action = str(result.get("action", "monitor"))
            if action not in {"allow", "monitor"}:
                self.enforcer.apply(
                    action,
                    reason=str(result.get("reason", action)),
                    channel=sensor.channel,
                    resource=sensor.resource,
                )

    def send_heartbeat(self) -> dict[str, Any]:
        sensors = self.profile.sensors
        metadata = {
            "endpoint_id": self.config.endpoint_id,
            "owner": self.config.owner,
            "site": self.config.site,
            "brand": BRAND["full_name"],
            "platform_id": self.profile.platform_id,
            "capabilities": list(self.profile.capabilities),
            "security_features": self.profile.security_features,
            "sensors": sensors,
            "vuln_probe": sensors.get("vuln_probe")
            or collect_vuln_probe(self.profile.security_features),
            "network_flows": sensors.get("network_flows") or [],
            "enforcement": self.enforcer.load().to_dict(),
        }
        payload = {
            "agent_id": self.config.agent_id,
            "agent_type": "endpoint",
            "hostname": self.profile.hostname,
            "os_name": self.profile.os_name,
            "version": __version__,
            "metadata": metadata,
        }
        return self._post("/api/agents/heartbeat", payload)

    def fetch_directives(self) -> dict[str, Any]:
        return self._get(f"/api/endpoints/{self.config.endpoint_id}/directives")

    def send_event(self, sensor: Any) -> dict[str, Any]:
        payload = {
            "endpoint_id": self.config.endpoint_id,
            "actor": self.config.owner or self.profile.username,
            "event_type": sensor.event_type,
            "channel": sensor.channel,
            "resource": sensor.resource,
            "classification": sensor.classification,
            "destination": sensor.destination,
            "process": sensor.process,
            "severity": sensor.severity,
            "behavior_flags": list(sensor.behavior_flags),
            "metadata": {"source": "mersal-agent", **sensor.metadata},
        }
        return self._post("/api/events", payload)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": f"MersalAgent/{__version__}"}
        if self.config.api_token:
            headers["X-Mersal-Token"] = self.config.api_token
        return headers

    def _ssl_context(self) -> ssl.SSLContext | None:
        cert = os.environ.get("MERSAL_AGENT_CERT", "").strip()
        key = os.environ.get("MERSAL_AGENT_KEY", "").strip()
        ca = os.environ.get("MERSAL_AGENT_CA", "").strip()
        if not cert or not key:
            return None
        ctx = ssl.create_default_context(cafile=ca or None)
        ctx.load_cert_chain(cert, key)
        return ctx

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.config.server}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15, context=self._ssl_context()) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    def _get(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.config.server}{path}",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=15, context=self._ssl_context()) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError:
            return {}
        except urllib.error.URLError:
            return {}

# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Mersal Endpoint Agent — continuous heartbeat, sensors, and enforcement."""

from __future__ import annotations

import hashlib
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
from .agent.event_queue import AgentEventQueue
from .brand import BRAND
from .config import agent_mtls_required
from .enforcement import LocalEnforcer
from .platform import collect_profile, collect_sensor_events
from .platform.vuln_probe import collect_vuln_probe
from .edr.ebpf_edr import collect_agent_ebpf_edr


@dataclass
class AgentConfig:
    server: str
    agent_id: str
    endpoint_id: str
    owner: str
    site: str
    interval_seconds: int
    api_token: str
    agent_api_key: str
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
            agent_api_key=str(payload.get("agent_api_key", os.environ.get("MERSAL_AGENT_API_KEY", ""))),
            state_dir=str(payload.get("state_dir", str(Path.home() / ".mersal-guard"))),
        )


class MersalAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state_dir = Path(config.state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.enforcer = LocalEnforcer(self.state_dir)
        self.queue = AgentEventQueue(self.state_dir)
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
        self._flush_queue()
        self.send_heartbeat()
        self.check_signed_updates()
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
            "queue_depth": self.queue.depth(),
        }
        ebpf_edr = collect_agent_ebpf_edr()
        metadata["ebpf_edr"] = ebpf_edr
        if ebpf_edr.get("edr_detections"):
            metadata["edr_detections"] = list(ebpf_edr.get("edr_detections", []))
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
        try:
            return self._post("/api/events", payload)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            self.queue.enqueue(payload)
            return {"action": "monitor", "queued": True}

    def check_signed_updates(self) -> dict[str, Any]:
        manifest = self._get("/api/updates/latest?component=agent")
        if not manifest.get("manifest_id"):
            return {}
        remote_version = str(manifest.get("version", ""))
        if remote_version == __version__:
            return {"skipped": True, "version": remote_version}
        artifact_url = str(manifest.get("artifact_url", ""))
        checksum = str(manifest.get("checksum_sha256", ""))
        if not artifact_url or not checksum:
            return {"error": "incomplete manifest"}
        try:
            request = urllib.request.Request(artifact_url, headers=self._headers())
            with urllib.request.urlopen(request, timeout=60, context=self._ssl_context()) as resp:  # noqa: S310
                data = resp.read()
        except (urllib.error.URLError, OSError) as exc:
            return {"error": str(exc)}
        digest = hashlib.sha256(data).hexdigest()
        if digest != checksum:
            return {"error": "checksum mismatch"}
        updates_dir = self.state_dir / "updates"
        updates_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = updates_dir / f"agent-{remote_version}.bin"
        artifact_path.write_bytes(data)
        (updates_dir / "pending.json").write_text(
            json.dumps({"version": remote_version, "path": str(artifact_path), "manifest": manifest}, indent=2),
            encoding="utf-8",
        )
        return {"staged": True, "version": remote_version, "path": str(artifact_path)}

    def _flush_queue(self) -> None:
        for item_id, payload in self.queue.pending():
            try:
                self._post("/api/events", payload)
                self.queue.ack(item_id)
            except (urllib.error.URLError, urllib.error.HTTPError, OSError):
                break

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "User-Agent": f"MersalAgent/{__version__}"}
        key = self.config.agent_api_key or self.config.api_token
        if key:
            headers["X-Mersal-Token"] = key
            headers["X-Mersal-Agent-Key"] = key
        headers["X-Mersal-Agent-Id"] = self.config.agent_id
        return headers

    def _ssl_context(self) -> ssl.SSLContext | None:
        cert = os.environ.get("MERSAL_AGENT_CERT", "").strip()
        key = os.environ.get("MERSAL_AGENT_KEY", "").strip()
        ca = os.environ.get("MERSAL_AGENT_CA", "").strip()
        if agent_mtls_required() and (not cert or not key):
            raise RuntimeError("MERSAL_AGENT_MTLS=1 requires MERSAL_AGENT_CERT and MERSAL_AGENT_KEY")
        if not cert or not key:
            return None
        ctx = ssl.create_default_context(cafile=ca or None)
        ctx.load_cert_chain(cert, key)
        if ca:
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED
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

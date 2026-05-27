"""HTTP API and admin dashboard for Extreme IP Guard."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .agents import supported_backends
from .storage import Database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = PROJECT_ROOT / "static"
DEFAULT_DB = PROJECT_ROOT / "data" / "extreme-ip-guard.sqlite3"


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, database: Database, **kwargs):
        self.database = database
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self.path = "/index.html"
            return super().do_GET()
        routes = {
            "/api/dashboard": self.database.dashboard,
            "/api/zones": self.database.list_zones,
            "/api/devices": self.database.list_devices,
            "/api/policies": self.database.list_policies,
            "/api/blocks": self.database.list_blocks,
            "/api/events": self.database.list_events,
            "/api/access-log": self.database.list_access_log,
            "/api/agents": self.database.list_agents,
            "/api/audit": self.database.list_audit,
            "/api/policy-bundle": self.database.get_policy_bundle,
            "/api/enforcement-backends": supported_backends,
        }
        if path in routes:
            return self._send_json(routes[path]())
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/evaluate":
                payload = self._read_json()
                return self._send_json(
                    self.database.evaluate(
                        source_ip=str(payload["source_ip"]),
                        destination_ip=str(payload.get("destination_ip", "0.0.0.0")),
                        destination_port=int(payload.get("destination_port", 0)),
                        protocol=str(payload.get("protocol", "tcp")),
                        zone=str(payload.get("zone", "default")),
                        device_id=payload.get("device_id"),
                    )
                )

            if path == "/api/devices":
                payload = self._read_json()
                return self._send_json(
                    self.database.register_device(
                        device_id=str(payload["device_id"]),
                        hostname=str(payload["hostname"]),
                        mac_address=str(payload.get("mac_address", "")),
                        ip_address=str(payload.get("ip_address", "")),
                        zone=str(payload.get("zone", "default")),
                        owner=str(payload.get("owner", "")),
                        device_type=str(payload.get("device_type", "workstation")),
                        tags=payload.get("tags"),
                    ),
                    status=HTTPStatus.CREATED,
                )

            if path.endswith("/approve") and path.startswith("/api/devices/"):
                device_id = self._path_segment(path, 2)
                return self._send_json(self.database.approve_device(device_id))

            if path == "/api/policies":
                return self._send_json(self.database.create_policy(self._read_json()), status=HTTPStatus.CREATED)

            if path == "/api/blocks":
                payload = self._read_json()
                return self._send_json(
                    self.database.create_block(
                        target=str(payload["target"]),
                        target_type=str(payload.get("target_type", "ip")),
                        reason=str(payload.get("reason", "Manual block")),
                        source=str(payload.get("source", "manual")),
                        severity=int(payload.get("severity", 50)),
                        ttl_hours=payload.get("ttl_hours"),
                        created_by=str(payload.get("created_by", "admin")),
                    ),
                    status=HTTPStatus.CREATED,
                )

            if path == "/api/events":
                payload = self._read_json()
                return self._send_json(
                    self.database.record_event(
                        event_type=str(payload["event_type"]),
                        source_ip=str(payload.get("source_ip", "")),
                        destination_ip=str(payload.get("destination_ip", "")),
                        severity=int(payload.get("severity", 10)),
                        details=payload.get("details"),
                        device_id=payload.get("device_id"),
                    ),
                    status=HTTPStatus.CREATED,
                )

            if path == "/api/flows":
                payload = self._read_json()
                return self._send_json(
                    self.database.ingest_flow(
                        source_ip=str(payload["source_ip"]),
                        destination_ip=str(payload["destination_ip"]),
                        destination_port=int(payload.get("destination_port", 0)),
                        protocol=str(payload.get("protocol", "tcp")),
                        bytes_sent=int(payload.get("bytes_sent", 0)),
                        packets=int(payload.get("packets", 1)),
                    )
                )

            if path == "/api/brute-force":
                payload = self._read_json()
                return self._send_json(
                    self.database.report_brute_force(
                        source_ip=str(payload["source_ip"]),
                        target_service=str(payload.get("target_service", "ssh")),
                        failed_attempts=int(payload["failed_attempts"]),
                    )
                )

            if path == "/api/agents/heartbeat":
                payload = self._read_json()
                return self._send_json(
                    self.database.record_agent_heartbeat(
                        agent_id=str(payload["agent_id"]),
                        agent_type=str(payload["agent_type"]),
                        hostname=str(payload["hostname"]),
                        os_name=str(payload.get("os_name", "")),
                        version=str(payload.get("version", "")),
                        metadata=payload.get("metadata", {}),
                    )
                )

            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except (KeyError, TypeError, ValueError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _read_json(self, default: dict | None = None) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {} if default is None else default
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def _send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _path_segment(path: str, index: int) -> str:
        parts = [part for part in path.split("/") if part]
        return parts[index]


def run(host: str = "127.0.0.1", port: int = 8090) -> None:
    database = Database(os.environ.get("EIPG_DB", DEFAULT_DB))
    database.init_schema()
    database.seed_demo()

    def handler(*args, **kwargs):
        RequestHandler(*args, database=database, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Extreme IP Guard running at http://{host}:{port}")
    server.serve_forever()

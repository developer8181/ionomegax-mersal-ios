"""Minimal HTTP API and dashboard server for Extreme IP Guard."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .agents import supported_control_profiles
from .storage import Database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = PROJECT_ROOT / "static"
DEFAULT_DB = PROJECT_ROOT / "data" / "extreme-ip-guard.sqlite3"


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, database: Database, **kwargs):
        self.database = database
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        path = urlparse(self.path).path
        if path == "/":
            self.path = "/index.html"
            return super().do_GET()
        if path == "/api/dashboard":
            return self._send_json(self.database.dashboard())
        if path == "/api/assets":
            return self._send_json(self.database.list_assets())
        if path == "/api/policies":
            return self._send_json(self.database.list_policies())
        if path == "/api/events":
            return self._send_json(self.database.list_events())
        if path == "/api/incidents":
            return self._send_json(self.database.list_incidents())
        if path == "/api/agents":
            return self._send_json(self.database.list_agents())
        if path == "/api/control-profiles":
            return self._send_json(supported_control_profiles())
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        path = urlparse(self.path).path
        try:
            if path == "/api/events":
                payload = self._read_json()
                event = self.database.ingest_event(
                    asset_id=int(payload["asset_id"]),
                    source_ip=str(payload.get("source_ip", "10.0.0.10")),
                    destination_ip=str(payload["destination_ip"]),
                    destination_port=int(payload["destination_port"]),
                    protocol=str(payload.get("protocol", "tcp")),
                    country=str(payload.get("country", "ZZ")),
                    bytes_out=int(payload.get("bytes_out", 0)),
                    bytes_in=int(payload.get("bytes_in", 0)),
                    process_name=str(payload.get("process_name", "")),
                    ip_reputation_score=int(payload.get("ip_reputation_score", 0)),
                    tor_exit_node=bool(payload.get("tor_exit_node", False)),
                    geo_anomaly=bool(payload.get("geo_anomaly", False)),
                    burst_connections=int(payload.get("burst_connections", 0)),
                )
                return self._send_json(event, status=HTTPStatus.CREATED)

            if path == "/api/agents/heartbeat":
                payload = self._read_json()
                agent = self.database.record_agent_heartbeat(
                    agent_id=str(payload["agent_id"]),
                    agent_type=str(payload["agent_type"]),
                    hostname=str(payload["hostname"]),
                    os_name=str(payload.get("os_name", "")),
                    version=str(payload.get("version", "")),
                    metadata=payload.get("metadata", {}),
                )
                return self._send_json(agent)

            if path.endswith("/quarantine") and path.startswith("/api/assets/"):
                payload = self._read_json(default={})
                asset = self.database.quarantine_asset(
                    self._path_id(path),
                    note=str(payload.get("note", "Manual quarantine from dashboard")),
                )
                return self._send_json(asset)

            if path.endswith("/resolve") and path.startswith("/api/incidents/"):
                payload = self._read_json(default={})
                incident = self.database.resolve_incident(
                    self._path_id(path),
                    note=str(payload.get("note", "Resolved from dashboard")),
                )
                return self._send_json(incident)

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
    def _path_id(path: str) -> int:
        parts = [part for part in path.split("/") if part]
        return int(parts[2])


def run(host: str = "127.0.0.1", port: int = 8090) -> None:
    database = Database(os.environ.get("XIPG_DB", DEFAULT_DB))
    database.init_schema()
    database.seed_demo()

    def handler(*args, **kwargs):
        RequestHandler(*args, database=database, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Extreme IP Guard running at http://{host}:{port}")
    server.serve_forever()

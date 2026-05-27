"""Minimal HTTP API and dashboard server for Extreme IP Guard."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

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
        if path == "/api/dlp-events":
            return self._send_json(self.database.list_dlp_events())
        if path == "/api/audit-log":
            return self._send_json(self.database.list_audit_log())
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        path = urlparse(self.path).path
        try:
            if path == "/api/assets/heartbeat":
                payload = self._read_json()
                asset = self.database.record_asset_heartbeat(
                    asset_id=str(payload["asset_id"]),
                    hostname=str(payload["hostname"]),
                    owner=str(payload.get("owner", "")),
                    department=str(payload.get("department", "General")),
                    ip_address=str(payload.get("ip_address", "")),
                    os_name=str(payload.get("os_name", "")),
                    agent_version=str(payload.get("agent_version", "")),
                    posture=payload.get("posture", {}),
                    metadata=payload.get("metadata", {}),
                )
                return self._send_json(asset, status=HTTPStatus.CREATED)

            if path == "/api/dlp-events":
                payload = self._read_json()
                event = self.database.record_dlp_event(
                    asset_ref=payload.get("asset_ref"),
                    username=str(payload.get("username", "")),
                    channel=str(payload["channel"]),
                    sensitivity=str(payload["sensitivity"]),
                    destination=str(payload.get("destination", "")),
                    destination_trusted=bool(payload.get("destination_trusted", False)),
                    bytes_count=int(payload.get("bytes_count", 0)),
                    encrypted=bool(payload.get("encrypted", False)),
                    user_override=bool(payload.get("user_override", False)),
                )
                return self._send_json(event, status=HTTPStatus.CREATED)

            if path.endswith("/isolate") and path.startswith("/api/assets/"):
                payload = self._read_json(default={})
                return self._send_json(self.database.isolate_asset(self._path_id(path), actor=str(payload.get("actor", "admin"))))

            if path.endswith("/restore") and path.startswith("/api/assets/"):
                payload = self._read_json(default={})
                return self._send_json(self.database.restore_asset(self._path_id(path), actor=str(payload.get("actor", "admin"))))

            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
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
    database = Database(os.environ.get("EIPG_DB", DEFAULT_DB))
    database.init_schema()
    database.seed_demo()

    def handler(*args, **kwargs):
        RequestHandler(*args, database=database, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Extreme IP Guard running at http://{host}:{port}")
    server.serve_forever()


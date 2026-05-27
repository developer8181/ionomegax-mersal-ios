"""HTTP API and SOC dashboard for Extreme IP Guard."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .agents import supported_agent_types
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
            "/api/endpoints": self.database.list_endpoints,
            "/api/agents": self.database.list_agents,
            "/api/events": self.database.list_events,
            "/api/incidents": self.database.list_incidents,
            "/api/policies": self.database.list_policies,
            "/api/audit": self.database.audit_status,
            "/api/agent-types": lambda: supported_agent_types(),
        }
        if path in routes:
            return self._send_json(routes[path]())
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/events":
                payload = self._read_json()
                result = self.database.ingest_event(payload)
                return self._send_json(result, status=HTTPStatus.CREATED)

            if path == "/api/agents/heartbeat":
                payload = self._read_json()
                return self._send_json(self.database.register_agent(payload))

            if path == "/api/zero-trust/check":
                payload = self._read_json()
                return self._send_json(self.database.zero_trust_check(payload))

            if path.endswith("/resolve") and path.startswith("/api/incidents/"):
                payload = self._read_json(default={})
                incident_id = self._path_id(path, suffix="/resolve")
                return self._send_json(
                    self.database.resolve_incident(
                        incident_id, str(payload.get("note", "Resolved via SOC"))
                    )
                )

            if path.endswith("/release") and path.startswith("/api/endpoints/"):
                endpoint_id = self._path_id(path, suffix="/release")
                return self._send_json(self.database.release_quarantine(endpoint_id))

            return self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
        except (KeyError, ValueError, TypeError) as exc:
            return self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _read_json(self, default: dict | None = None) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return default or {}
        return json.loads(self.rfile.read(length))

    def _send_json(self, payload: object, *, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _path_id(self, path: str, *, suffix: str) -> int:
        middle = path.removeprefix("/api/").removesuffix(suffix)
        parts = middle.split("/")
        return int(parts[-1])

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def run(host: str = "127.0.0.1", port: int = 8090) -> None:
    db_path = os.environ.get("EIG_DB", str(DEFAULT_DB))
    database = Database(db_path)
    database.init_schema()
    database.seed_demo()

    def handler(*args, **kwargs):
        return RequestHandler(*args, database=database, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Extreme IP Guard SOC console: http://{host}:{port}")
    print(f"Database: {db_path}")
    server.serve_forever()

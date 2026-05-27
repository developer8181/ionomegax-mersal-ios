"""Minimal HTTP API for the Xtreme IP Guard prototype."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .core import EndpointEvent, PolicyRule
from .storage import Database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "xtreme-ip-guard.sqlite3"


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, database: Database, **kwargs):
        self.database = database
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        path = urlparse(self.path).path
        if path == "/":
            return self._send_json(
                {
                    "name": "Xtreme IP Guard",
                    "status": "running",
                    "endpoints": ["/api/dashboard", "/api/endpoints", "/api/events", "/api/policies", "/api/agents"],
                }
            )
        if path == "/api/dashboard":
            return self._send_json(self.database.dashboard())
        if path == "/api/endpoints":
            return self._send_json(self.database.list_endpoints())
        if path == "/api/events":
            return self._send_json(self.database.list_events())
        if path == "/api/policies":
            return self._send_json(self.database.list_policies())
        if path == "/api/agents":
            return self._send_json(self.database.list_agents())
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        path = urlparse(self.path).path
        try:
            if path == "/api/agents/heartbeat":
                payload = self._read_json()
                agent = self.database.record_agent_heartbeat(
                    agent_id=str(payload["agent_id"]),
                    agent_type=str(payload.get("agent_type", "endpoint")),
                    hostname=str(payload["hostname"]),
                    os_name=str(payload.get("os_name", "")),
                    version=str(payload.get("version", "")),
                    metadata=dict(payload.get("metadata", {})),
                )
                return self._send_json(agent)

            if path == "/api/events":
                payload = self._read_json()
                event = EndpointEvent(
                    endpoint_id=str(payload["endpoint_id"]),
                    actor=str(payload["actor"]),
                    event_type=str(payload["event_type"]),
                    channel=str(payload["channel"]),
                    resource=str(payload["resource"]),
                    classification=str(payload.get("classification", "internal")),
                    destination=str(payload.get("destination", "")),
                    process=str(payload.get("process", "")),
                    severity=int(payload.get("severity", 10)),
                    behavior_flags=tuple(payload.get("behavior_flags", [])),
                    metadata=dict(payload.get("metadata", {})),
                )
                return self._send_json(self.database.ingest_event(event), status=HTTPStatus.CREATED)

            if path == "/api/policies":
                payload = self._read_json()
                policy = PolicyRule(
                    rule_id=str(payload["rule_id"]),
                    name=str(payload["name"]),
                    action=str(payload["action"]),
                    event_type=str(payload.get("event_type", "*")),
                    classification=str(payload.get("classification", "*")),
                    channel=str(payload.get("channel", "*")),
                    destination_contains=str(payload.get("destination_contains", "")),
                    min_risk=int(payload.get("min_risk", 0)),
                    reason=str(payload.get("reason", "")),
                    enabled=bool(payload.get("enabled", True)),
                )
                return self._send_json(self.database.create_policy(policy), status=HTTPStatus.CREATED)

            if path.startswith("/api/endpoints/") and path.endswith("/isolate"):
                endpoint_id = self._path_part(path, 2)
                return self._send_json(self.database.set_endpoint_isolation(endpoint_id, True))

            if path.startswith("/api/endpoints/") and path.endswith("/restore"):
                endpoint_id = self._path_part(path, 2)
                return self._send_json(self.database.set_endpoint_isolation(endpoint_id, False))

            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: object) -> None:
        """Keep prototype output readable during tests and demos."""

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def _send_json(self, data: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _path_part(path: str, index: int) -> str:
        parts = [part for part in path.split("/") if part]
        return parts[index]


def run(host: str = "127.0.0.1", port: int = 8090) -> None:
    database = Database(os.environ.get("XIG_DB", DEFAULT_DB))
    database.init_schema()
    database.seed_demo()

    def handler(*args, **kwargs):
        RequestHandler(*args, database=database, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Xtreme IP Guard running at http://{host}:{port}")
    server.serve_forever()

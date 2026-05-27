"""Ionomegax Mersal Guard — HTTP API and Command Center."""

from __future__ import annotations

import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .auth import authorize
from .brand import BRAND
from .core import EndpointEvent, PolicyRule
from .storage import Database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "mersal-guard.sqlite3"
WEB_ROOT = PROJECT_ROOT / "web"


class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, database: Database, **kwargs):
        self.database = database
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/", "/console", "/console/"}:
            return self._serve_file(WEB_ROOT / "index.html")
        if path.startswith("/console/"):
            return self._serve_file(WEB_ROOT / path.removeprefix("/console/"))
        if not self._authorized():
            return
        if path == "/api/health":
            return self._send_json({"status": "ok", "product": BRAND["full_name"]})
        if path == "/api/brand":
            return self._send_json(BRAND)
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
        if path.startswith("/api/endpoints/") and path.endswith("/directives"):
            endpoint_id = self._path_part(path, 2)
            return self._send_json(self.database.endpoint_directives(endpoint_id))
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")

    def do_POST(self) -> None:  # noqa: N802
        if not self._authorized():
            return
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
        return

    def _authorized(self) -> bool:
        token = self.headers.get("X-Mersal-Token") or self.headers.get("Authorization", "").removeprefix("Bearer ")
        if authorize(token):
            return True
        self._send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
        return False

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

    def _serve_file(self, relative: Path) -> None:
        target = relative
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            target = WEB_ROOT / "index.html"
        resolved = target.resolve()
        web_root = WEB_ROOT.resolve()
        if web_root not in resolved.parents and resolved != web_root / "index.html":
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        content_type, _ = mimetypes.guess_type(str(resolved))
        body = resolved.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @staticmethod
    def _path_part(path: str, index: int) -> str:
        parts = [part for part in path.split("/") if part]
        return parts[index]


def run(host: str | None = None, port: int | None = None) -> None:
    bind_host = host or os.environ.get("MERSAL_HOST", "0.0.0.0")
    bind_port = port or int(os.environ.get("MERSAL_PORT", "8090"))
    database = Database(os.environ.get("MERSAL_DB", os.environ.get("XIG_DB", DEFAULT_DB)))
    database.init_schema()
    database.seed_demo()

    def handler(*args, **kwargs):
        RequestHandler(*args, database=database, **kwargs)

    server = ThreadingHTTPServer((bind_host, bind_port), handler)
    token = os.environ.get("MERSAL_API_TOKEN", "")
    print(f"{BRAND['full_name']} running at http://{bind_host}:{bind_port}")
    print(f"Command Center: http://{bind_host}:{bind_port}/console/")
    if token:
        print("API token authentication is enabled (X-Mersal-Token header).")
    server.serve_forever()

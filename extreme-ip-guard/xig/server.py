"""HTTP control plane for Extreme IP Guard.

The server exposes a small REST surface (no external dependencies) over
:class:`http.server.ThreadingHTTPServer`. It is deliberately small so the
reference implementation is auditable from end to end.

For production this layer should be replaced with a battle-tested framework
(FastAPI, Actix-Web), but the routing table here is the contract every
client (agent, console UI, CLI) speaks to today.
"""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from .core import TelemetryEvent
from .storage import Database


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = PROJECT_ROOT / "static"
DEFAULT_DB = PROJECT_ROOT / "data" / "extreme-ip-guard.sqlite3"


class _Handler(SimpleHTTPRequestHandler):
    server_version = "ExtremeIPGuard/0.1"

    def __init__(self, *args: Any, database: Database, **kwargs: Any) -> None:
        self.database = database
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    # ---- routing ----

    def do_GET(self) -> None:  # noqa: N802 - stdlib name
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path in {"", "/"}:
            self.path = "/index.html"
            return super().do_GET()

        routes = {
            "/api/dashboard": lambda: self._json(self.database.dashboard()),
            "/api/users": lambda: self._json(self.database.list_users()),
            "/api/assets": lambda: self._json(self.database.list_assets()),
            "/api/agents": lambda: self._json(self.database.list_agents()),
            "/api/alerts": lambda: self._json(self.database.list_alerts()),
            "/api/events": lambda: self._json(self.database.list_events()),
            "/api/policies": lambda: self._json(self.database.list_policies()),
            "/api/iocs": lambda: self._json(self.database.list_iocs()),
            "/api/audit": lambda: self._json(self.database.list_audit_entries()),
            "/api/audit/verify": lambda: self._json(self.database.verify_audit_chain()),
            "/api/events/verify": lambda: self._json(self.database.verify_event_chain()),
        }
        if path in routes:
            return routes[path]()

        if path == "/api/commands":
            agent_id = (query.get("agent_id") or [""])[0]
            status = (query.get("status") or [""])[0]
            return self._json(self.database.list_commands(agent_id or None, status or None))

        if path == "/api/agents/poll":
            agent_id = (query.get("agent_id") or [""])[0]
            if not agent_id:
                return self._error(HTTPStatus.BAD_REQUEST, "agent_id is required")
            return self._json(self.database.fetch_pending_commands(agent_id))

        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib name
        path = urlparse(self.path).path
        try:
            if path == "/api/agents/enrol-tokens":
                payload = self._read_json()
                return self._json(
                    self.database.issue_enrol_token(
                        hostname=str(payload["hostname"]).strip(),
                        criticality=str(payload.get("criticality", "normal")),
                        actor=str(payload.get("actor", "console")),
                    ),
                    status=HTTPStatus.CREATED,
                )

            if path == "/api/agents/enrol":
                payload = self._read_json()
                return self._json(
                    self.database.enrol_agent(
                        enrol_token=str(payload["enrol_token"]),
                        agent_id=str(payload["agent_id"]),
                        hw_fp=str(payload.get("hw_fp", "")),
                        os_name=str(payload.get("os_name", "")),
                        version=str(payload.get("version", "")),
                    ),
                    status=HTTPStatus.CREATED,
                )

            if path == "/api/agents/heartbeat":
                payload = self._read_json()
                return self._json(
                    self.database.record_heartbeat(
                        agent_id=str(payload["agent_id"]),
                        version=str(payload.get("version", "")),
                    )
                )

            if path == "/api/events":
                payload = self._read_json()
                event = TelemetryEvent(
                    agent_id=str(payload["agent_id"]),
                    kind=str(payload["kind"]),
                    ts=str(payload.get("ts") or ""),
                    subject=str(payload.get("subject", "")),
                    data=dict(payload.get("data") or {}),
                )
                if not event.ts:
                    from .core import utc_now_iso

                    event = TelemetryEvent(
                        agent_id=event.agent_id,
                        kind=event.kind,
                        ts=utc_now_iso(),
                        subject=event.subject,
                        data=event.data,
                    )
                user_id = payload.get("user_id")
                return self._json(
                    self.database.ingest_event(event, user_id=int(user_id) if user_id else None),
                    status=HTTPStatus.CREATED,
                )

            if path == "/api/commands/complete":
                payload = self._read_json()
                return self._json(
                    self.database.complete_command(
                        command_uid=str(payload["command_uid"]),
                        status=str(payload["status"]),
                        result=dict(payload.get("result") or {}),
                        actor=str(payload.get("actor", "agent")),
                    )
                )

            if path == "/api/iocs":
                payload = self._read_json()
                return self._json(
                    self.database.add_ioc(
                        kind=str(payload["kind"]),
                        value=str(payload["value"]),
                        source=str(payload.get("source", "console")),
                        actor=str(payload.get("actor", "console")),
                    ),
                    status=HTTPStatus.CREATED,
                )

            if path == "/api/policies/publish":
                return self._json(self.database.publish_default_policy(actor="console"), status=HTTPStatus.CREATED)

            if path.startswith("/api/alerts/") and path.endswith("/status"):
                alert_uid = path.split("/")[3]
                payload = self._read_json()
                return self._json(
                    self.database.update_alert_status(
                        alert_uid=alert_uid,
                        status=str(payload["status"]),
                        actor=str(payload.get("actor", "console")),
                    )
                )

            if path == "/api/auth/login":
                payload = self._read_json()
                user = self.database.authenticate(str(payload.get("username", "")), str(payload.get("password", "")))
                if user is None:
                    return self._error(HTTPStatus.UNAUTHORIZED, "invalid credentials")
                return self._json(user)

            return self._error(HTTPStatus.NOT_FOUND, "unknown endpoint")
        except (KeyError, TypeError, ValueError) as exc:
            return self._error(HTTPStatus.BAD_REQUEST, str(exc))

    # ---- helpers ----

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    def _json(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _error(self, status: HTTPStatus, message: str) -> None:
        self._json({"error": message}, status=status)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib name
        if os.environ.get("XIG_QUIET"):
            return
        super().log_message(format, *args)


def build_database() -> Database:
    db_path = os.environ.get("XIG_DB", str(DEFAULT_DB))
    database = Database(db_path)
    database.init_schema()
    database.seed_demo()
    return database


def run(host: str = "127.0.0.1", port: int = 8090) -> None:
    database = build_database()

    def factory(*args: Any, **kwargs: Any) -> _Handler:
        return _Handler(*args, database=database, **kwargs)

    server = ThreadingHTTPServer((host, port), factory)
    print(f"Extreme IP Guard control plane listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

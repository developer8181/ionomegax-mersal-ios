"""HTTP API and static-file server for Extreme Print Management System."""

from __future__ import annotations

import json
import os
import ssl
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .agents import supported_platforms
from .auth import SESSION_COOKIE, SESSION_HEADER, user_to_dict
from .config import Settings
from .core import money_to_cents
from .policy import scrub_job_document
from .security import AGENT_TOKEN_HEADER, is_authorized_agent_token
from .storage import Database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = PROJECT_ROOT / "static"
RELEASE_ROOT = PROJECT_ROOT / "release_station"
DEFAULT_DB = PROJECT_ROOT / "data" / "extreme-print-management.sqlite3"


class RequestHandler(SimpleHTTPRequestHandler):
    def __init__(
        self,
        *args,
        database: Database,
        settings: Settings,
        **kwargs,
    ):
        self.database = database
        self.settings = settings
        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self.path = "/index.html"
            return super().do_GET()
        if path == "/release" or path == "/release/":
            return self._serve_release_station("index.html")
        if path.startswith("/release/"):
            return self._serve_release_station(path.removeprefix("/release/"))
        if path == "/api/auth/me":
            return self._handle_auth_me()
        if path == "/api/dashboard":
            return self._send_json(self.database.dashboard())
        if path == "/api/users":
            return self._send_json(self.database.list_users())
        if path == "/api/printers":
            return self._send_json(self.database.list_printers())
        if path == "/api/jobs":
            return self._send_json(self.database.list_jobs())
        if path == "/api/agents":
            return self._send_json(self.database.list_agents())
        if path == "/api/audit-logs":
            return self._require_permission("view", lambda: self._send_json(self.database.list_audit_logs()))
        if path == "/api/pricing-rules":
            return self._require_permission("view", lambda: self._send_json(self.database.list_pricing_rules()))
        if path == "/api/printer-platforms":
            return self._send_json(supported_platforms())
        if path == "/api/settings":
            return self._require_permission("manage_settings", lambda: self._send_json(self._settings_payload()))
        if path == "/api/readiness":
            return self._readiness()
        if path.startswith("/api/release/held/"):
            username = path.rsplit("/", 1)[-1]
            return self._send_json(self.database.list_held_jobs_for_user(username=username))
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/auth/login":
                return self._login()
            if path == "/api/auth/logout":
                return self._logout()
            if path == "/api/jobs":
                return self._submit_job()
            if path.endswith("/release") and path.startswith("/api/jobs/"):
                return self._require_permission(
                    "manage_jobs",
                    lambda: self._send_json(self._scrub_job(self.database.release_job(self._path_id(path)))),
                )
            if path.endswith("/deny") and path.startswith("/api/jobs/"):
                payload = self._read_json(default={})
                return self._require_permission(
                    "manage_jobs",
                    lambda: self._send_json(
                        self._scrub_job(
                            self.database.deny_job(self._path_id(path), str(payload.get("reason", "Denied by administrator")))
                        )
                    ),
                )
            if path.endswith("/credit") and path.startswith("/api/users/"):
                payload = self._read_json()
                return self._require_permission(
                    "manage_users",
                    lambda: self._send_json(
                        self.database.add_credit(
                            self._path_id(path),
                            money_to_cents(payload["amount"]),
                            str(payload.get("note", "Manual credit")),
                        )
                    ),
                )
            if path == "/api/quotas/reset":
                return self._require_permission("manage_users", lambda: self._send_json(self.database.reset_monthly_quotas()))
            if path == "/api/agents/heartbeat":
                if not self._require_agent_auth():
                    return
                payload = self._read_json()
                agent = self.database.record_agent_heartbeat(
                    agent_id=str(payload["agent_id"]),
                    agent_type=str(payload["agent_type"]),
                    hostname=str(payload["hostname"]),
                    os_name=str(payload.get("os_name", ""),
                    version=str(payload.get("version", ""),
                    metadata=payload.get("metadata", {}),
                )
                return self._send_json(agent)
            if path == "/api/pricing-rules":
                payload = self._read_json()
                return self._require_permission(
                    "manage_pricing",
                    lambda: self._send_json(
                        self.database.upsert_pricing_rule(
                            department=str(payload["department"]),
                            bw_multiplier_percent=int(payload.get("bw_multiplier_percent", 100)),
                            color_multiplier_percent=int(payload.get("color_multiplier_percent", 100)),
                            duplex_discount_override=(
                                int(payload["duplex_discount_override"])
                                if payload.get("duplex_discount_override") is not None
                                else None
                            ),
                            is_active=bool(payload.get("is_active", True)),
                        )
                    ),
                )
            if path == "/api/audit-logs/purge":
                return self._require_permission(
                    "manage_settings",
                    lambda: self._send_json(self.database.purge_expired_audit_logs()),
                )
            if path == "/api/demo/reset":
                return self._require_permission("demo_reset", lambda: self._send_json(self.database.seed_enterprise_demo()))
            if path.startswith("/api/release/jobs/") and path.endswith("/release"):
                parts = [part for part in path.split("/") if part]
                job_id = int(parts[3])
                payload = self._read_json()
                username = str(payload.get("username", ""))
                return self._send_json(self._scrub_job(self.database.release_job_as_user(job_id, username=username)))
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except (KeyError, TypeError, ValueError) as exc:
            self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

    def _readiness(self) -> None:
        dashboard = self.database.dashboard()
        self._send_json(
            {
                "product": "Extreme Print Management System",
                "edition": "Production",
                "status": "production_ready",
                "auth_required": self.settings.require_auth,
                "agent_token_enforced": bool(self.settings.agent_token),
                "anonymize_documents": self.settings.anonymize_documents,
                "components": dashboard["readiness"],
                "capabilities": [
                    "rbac",
                    "department_pricing",
                    "audit_retention",
                    "site_server_sync",
                    "cups_provider",
                    "windows_spooler_adapter",
                    "release_station",
                    "optional_tls",
                ],
            }
        )

    def _settings_payload(self) -> dict:
        return {
            "anonymize_documents": self.settings.anonymize_documents,
            "audit_retention_days": self.settings.audit_retention_days,
            "require_auth": self.settings.require_auth,
            "site_id": self.settings.site_id,
            "custom": self.database.get_setting("custom", {}),
        }

    def _login(self) -> None:
        payload = self._read_json()
        token, user = self.database.authenticate_admin(
            username=str(payload["username"]),
            password=str(payload["password"]),
        )
        body = {"token": token, "user": user_to_dict(user)}
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Set-Cookie", f"{SESSION_COOKIE}={token}; HttpOnly; Path=/; SameSite=Lax")
        self.end_headers()
        self.wfile.write(encoded)

    def _logout(self) -> None:
        token = self._session_token()
        if token:
            self.database.logout_session(token)
        self._send_json({"ok": True})

    def _handle_auth_me(self) -> None:
        user = self._current_user()
        if user is None:
            return self._send_json({"authenticated": False})
        self._send_json({"authenticated": True, "user": user_to_dict(user)})

    def _submit_job(self) -> None:
        payload = self._read_json()
        source = str(payload.get("source", "web"))
        agent_id = str(payload.get("agent_id", ""))
        if (source != "web" or agent_id) and not self._require_agent_auth():
            return
        job = self.database.submit_job(
            user_id=int(payload["user_id"]),
            printer_id=int(payload["printer_id"]),
            document_name=str(payload.get("document_name", "")),
            pages=int(payload["pages"]),
            copies=int(payload.get("copies", 1)),
            color=bool(payload.get("color", False)),
            duplex=bool(payload.get("duplex", False)),
            account=str(payload.get("account", "Personal")),
            source=source,
            agent_id=agent_id,
        )
        self._send_json(self._scrub_job(job), status=HTTPStatus.CREATED)

    def _serve_release_station(self, filename: str) -> None:
        path = (RELEASE_ROOT / filename).resolve()
        if not str(path).startswith(str(RELEASE_ROOT.resolve())) or not path.exists():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = path.read_bytes()
        content_type = "text/html; charset=utf-8"
        if path.suffix == ".js":
            content_type = "application/javascript; charset=utf-8"
        elif path.suffix == ".css":
            content_type = "text/css; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _current_user(self):
        return self.database.resolve_session(self._session_token())

    def _session_token(self) -> str | None:
        header = self.headers.get(SESSION_HEADER, "").strip()
        if header:
            return header
        cookie_header = self.headers.get("Cookie", "")
        if not cookie_header:
            return None
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        morsel = cookies.get(SESSION_COOKIE)
        return morsel.value if morsel else None

    def _require_permission(self, permission: str, handler):
        if not self.settings.require_auth:
            return handler()
        user = self._current_user()
        if user is None:
            return self._send_json({"error": "authentication required"}, status=HTTPStatus.UNAUTHORIZED)
        if not user.has_permission(permission):
            return self._send_json({"error": "permission denied"}, status=HTTPStatus.FORBIDDEN)
        return handler()

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

    def _require_agent_auth(self) -> bool:
        provided = self.headers.get(AGENT_TOKEN_HEADER)
        if is_authorized_agent_token(provided, self.settings.agent_token):
            return True
        self._send_json({"error": "agent token is required or invalid"}, status=HTTPStatus.UNAUTHORIZED)
        return False

    def _scrub_job(self, job: dict) -> dict:
        return scrub_job_document(job, enabled=self.settings.anonymize_documents)

    @staticmethod
    def _path_id(path: str) -> int:
        parts = [part for part in path.split("/") if part]
        return int(parts[2])


def create_database(settings: Settings) -> Database:
    if settings.pg_dsn:
        raise RuntimeError(
            "EPMS_PG_DSN is set but the application currently runs on SQLite. "
            "Use deploy/postgres/schema.sql for external PostgreSQL and point EPMS_DB to SQLite, "
            "or remove EPMS_PG_DSN until the native driver port is enabled."
        )
    return Database(
        settings.db_path,
        anonymize_documents=settings.anonymize_documents,
        audit_retention_days=settings.audit_retention_days,
    )


def run(host: str | None = None, port: int | None = None) -> None:
    settings = Settings.from_environ(project_root=PROJECT_ROOT, default_db=DEFAULT_DB)
    host = host or settings.host
    port = port or settings.port

    database = create_database(settings)
    database.init_schema()
    database.seed_demo()
    database.purge_expired_audit_logs()
    bootstrap = database.bootstrap_admin(password=settings.bootstrap_admin_password)
    if bootstrap:
        print(f"[EPMS] Bootstrap admin created: {bootstrap['username']} (change password immediately)")

    def handler(*args, **kwargs):
        RequestHandler(*args, database=database, settings=settings, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    protocol = "http"
    if settings.tls_cert and settings.tls_key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=str(settings.tls_cert), keyfile=str(settings.tls_key))
        server.socket = context.wrap_socket(server.socket, server_side=True)
        protocol = "https"

    print(f"Extreme Print Management System running at {protocol}://{host}:{port}")
    if settings.require_auth:
        print("[EPMS] Admin authentication is required for privileged API actions")
    server.serve_forever()


def run_from_env() -> None:
    run()

"""Minimal HTTP API and static-file server for the print management dashboard."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .core import money_to_cents
from .storage import Database

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_ROOT = PROJECT_ROOT / "static"
DEFAULT_DB = PROJECT_ROOT / "data" / "extreme-print-management.sqlite3"


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
        if path == "/api/users":
            return self._send_json(self.database.list_users())
        if path == "/api/printers":
            return self._send_json(self.database.list_printers())
        if path == "/api/jobs":
            return self._send_json(self.database.list_jobs())
        return super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        path = urlparse(self.path).path
        try:
            if path == "/api/jobs":
                payload = self._read_json()
                job = self.database.submit_job(
                    user_id=int(payload["user_id"]),
                    printer_id=int(payload["printer_id"]),
                    document_name=str(payload.get("document_name", "")),
                    pages=int(payload["pages"]),
                    copies=int(payload.get("copies", 1)),
                    color=bool(payload.get("color", False)),
                    duplex=bool(payload.get("duplex", False)),
                    account=str(payload.get("account", "Personal")),
                )
                return self._send_json(job, status=HTTPStatus.CREATED)

            if path.endswith("/release") and path.startswith("/api/jobs/"):
                return self._send_json(self.database.release_job(self._path_id(path)))

            if path.endswith("/deny") and path.startswith("/api/jobs/"):
                payload = self._read_json(default={})
                return self._send_json(self.database.deny_job(self._path_id(path), str(payload.get("reason", "Denied by administrator"))))

            if path.endswith("/credit") and path.startswith("/api/users/"):
                payload = self._read_json()
                user = self.database.add_credit(
                    self._path_id(path),
                    money_to_cents(payload["amount"]),
                    str(payload.get("note", "Manual credit")),
                )
                return self._send_json(user)

            if path == "/api/quotas/reset":
                return self._send_json(self.database.reset_monthly_quotas())

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


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    database = Database(os.environ.get("EPMS_DB", DEFAULT_DB))
    database.init_schema()
    database.seed_demo()

    def handler(*args, **kwargs):
        RequestHandler(*args, database=database, **kwargs)

    server = ThreadingHTTPServer((host, port), handler)
    print(f"Extreme Print Management System running at http://{host}:{port}")
    server.serve_forever()

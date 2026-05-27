"""Small private print management server.

This module intentionally uses only the Python standard library so the MVP can
run in restricted on-premise environments without pulling external packages.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp."""

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_bool(value: Any) -> bool:
    """Accept JSON-friendly boolean values."""

    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


@dataclass(frozen=True)
class AppConfig:
    db_path: Path
    host: str = "127.0.0.1"
    port: int = 8080


class PrintManagementStore:
    """Persistence and business rules for private print management."""

    TERMINAL_JOB_STATES = {"released", "cancelled", "rejected"}

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_schema(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    quota_pages INTEGER NOT NULL CHECK (quota_pages >= 0),
                    used_pages INTEGER NOT NULL DEFAULT 0 CHECK (used_pages >= 0),
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS printers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    location TEXT NOT NULL DEFAULT '',
                    supports_color INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS print_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    printer_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    pages INTEGER NOT NULL CHECK (pages > 0),
                    copies INTEGER NOT NULL CHECK (copies > 0),
                    color INTEGER NOT NULL DEFAULT 0,
                    duplex INTEGER NOT NULL DEFAULT 0,
                    charged_pages INTEGER NOT NULL CHECK (charged_pages > 0),
                    estimated_sheets INTEGER NOT NULL CHECK (estimated_sheets > 0),
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(printer_id) REFERENCES printers(id)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL DEFAULT 'system',
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def create_user(
        self,
        username: str,
        display_name: str | None = None,
        quota_pages: int = 100,
    ) -> dict[str, Any]:
        username = username.strip().lower()
        if not username:
            raise ValueError("username is required")
        quota_pages = int(quota_pages)
        if quota_pages < 0:
            raise ValueError("quota_pages must be zero or greater")
        display_name = (display_name or username).strip()

        with self._lock, self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO users (username, display_name, quota_pages, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, display_name, quota_pages, utc_now()),
            )
            self._audit(conn, "user.created", "admin", {"user_id": cursor.lastrowid})
            return self.get_user(cursor.lastrowid, conn=conn)

    def get_user(
        self, user_id: int, conn: sqlite3.Connection | None = None
    ) -> dict[str, Any]:
        own_connection = conn is None
        conn = conn or self.connect()
        try:
            row = conn.execute(
                """
                SELECT
                    id,
                    username,
                    display_name,
                    quota_pages,
                    used_pages,
                    quota_pages - used_pages AS remaining_pages,
                    is_active,
                    created_at
                FROM users
                WHERE id = ?
                """,
                (int(user_id),),
            ).fetchone()
            if row is None:
                raise LookupError("user not found")
            return row_to_dict(row)
        finally:
            if own_connection:
                conn.close()

    def list_users(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    id,
                    username,
                    display_name,
                    quota_pages,
                    used_pages,
                    quota_pages - used_pages AS remaining_pages,
                    is_active,
                    created_at
                FROM users
                ORDER BY username
                """
            ).fetchall()
            return [row_to_dict(row) for row in rows]

    def create_printer(
        self,
        name: str,
        location: str = "",
        supports_color: bool = False,
    ) -> dict[str, Any]:
        name = name.strip()
        if not name:
            raise ValueError("printer name is required")

        with self._lock, self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO printers (name, location, supports_color, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (name, location.strip(), int(supports_color), utc_now()),
            )
            self._audit(
                conn, "printer.created", "admin", {"printer_id": cursor.lastrowid}
            )
            return self.get_printer(cursor.lastrowid, conn=conn)

    def get_printer(
        self, printer_id: int, conn: sqlite3.Connection | None = None
    ) -> dict[str, Any]:
        own_connection = conn is None
        conn = conn or self.connect()
        try:
            row = conn.execute(
                """
                SELECT id, name, location, supports_color, is_active, created_at
                FROM printers
                WHERE id = ?
                """,
                (int(printer_id),),
            ).fetchone()
            if row is None:
                raise LookupError("printer not found")
            return row_to_dict(row)
        finally:
            if own_connection:
                conn.close()

    def list_printers(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT id, name, location, supports_color, is_active, created_at
                FROM printers
                ORDER BY name
                """
            ).fetchall()
            return [row_to_dict(row) for row in rows]

    def submit_job(
        self,
        user_id: int,
        printer_id: int,
        title: str,
        pages: int,
        copies: int = 1,
        color: bool = False,
        duplex: bool = False,
    ) -> dict[str, Any]:
        title = title.strip()
        if not title:
            raise ValueError("job title is required")

        pages = int(pages)
        copies = int(copies)
        if pages <= 0:
            raise ValueError("pages must be greater than zero")
        if copies <= 0:
            raise ValueError("copies must be greater than zero")

        with self._lock, self.connect() as conn:
            user = self.get_user(int(user_id), conn=conn)
            printer = self.get_printer(int(printer_id), conn=conn)

            if not user["is_active"]:
                status = "rejected"
                reason = "inactive_user"
            elif not printer["is_active"]:
                status = "rejected"
                reason = "inactive_printer"
            elif color and not printer["supports_color"]:
                status = "rejected"
                reason = "printer_does_not_support_color"
            else:
                status = "queued"
                reason = ""

            charged_pages = self.calculate_charged_pages(pages, copies, color)
            estimated_sheets = self.calculate_estimated_sheets(pages, copies, duplex)

            if status == "queued" and user["remaining_pages"] < charged_pages:
                status = "rejected"
                reason = "quota_exceeded"

            now = utc_now()
            cursor = conn.execute(
                """
                INSERT INTO print_jobs (
                    user_id,
                    printer_id,
                    title,
                    pages,
                    copies,
                    color,
                    duplex,
                    charged_pages,
                    estimated_sheets,
                    status,
                    reason,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(user_id),
                    int(printer_id),
                    title,
                    pages,
                    copies,
                    int(color),
                    int(duplex),
                    charged_pages,
                    estimated_sheets,
                    status,
                    reason,
                    now,
                    now,
                ),
            )

            if status == "queued":
                conn.execute(
                    "UPDATE users SET used_pages = used_pages + ? WHERE id = ?",
                    (charged_pages, int(user_id)),
                )

            self._audit(
                conn,
                "job.submitted",
                user["username"],
                {
                    "job_id": cursor.lastrowid,
                    "status": status,
                    "charged_pages": charged_pages,
                    "reason": reason,
                },
            )
            return self.get_job(cursor.lastrowid, conn=conn)

    def get_job(
        self, job_id: int, conn: sqlite3.Connection | None = None
    ) -> dict[str, Any]:
        own_connection = conn is None
        conn = conn or self.connect()
        try:
            row = conn.execute(
                self._job_select_sql("WHERE jobs.id = ?"),
                (int(job_id),),
            ).fetchone()
            if row is None:
                raise LookupError("job not found")
            return row_to_dict(row)
        finally:
            if own_connection:
                conn.close()

    def list_jobs(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                self._job_select_sql("ORDER BY jobs.id DESC")
            ).fetchall()
            return [row_to_dict(row) for row in rows]

    def update_job_status(
        self, job_id: int, status: str, actor: str = "admin"
    ) -> dict[str, Any]:
        status = status.strip().lower()
        if status not in {"released", "cancelled"}:
            raise ValueError("status must be released or cancelled")

        with self._lock, self.connect() as conn:
            job = self.get_job(job_id, conn=conn)
            if job["status"] in self.TERMINAL_JOB_STATES:
                raise ValueError("job is already terminal")
            if job["status"] != "queued":
                raise ValueError("only queued jobs can be updated")

            conn.execute(
                """
                UPDATE print_jobs
                SET status = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, utc_now(), int(job_id)),
            )
            if status == "cancelled":
                conn.execute(
                    "UPDATE users SET used_pages = used_pages - ? WHERE id = ?",
                    (job["charged_pages"], job["user_id"]),
                )
            self._audit(
                conn,
                f"job.{status}",
                actor,
                {"job_id": int(job_id), "charged_pages": job["charged_pages"]},
            )
            return self.get_job(job_id, conn=conn)

    @staticmethod
    def calculate_charged_pages(pages: int, copies: int, color: bool) -> int:
        color_multiplier = 2 if color else 1
        return int(pages) * int(copies) * color_multiplier

    @staticmethod
    def calculate_estimated_sheets(pages: int, copies: int, duplex: bool) -> int:
        sheets_per_copy = math.ceil(int(pages) / 2) if duplex else int(pages)
        return sheets_per_copy * int(copies)

    def _audit(
        self,
        conn: sqlite3.Connection,
        event_type: str,
        actor: str,
        details: dict[str, Any],
    ) -> None:
        conn.execute(
            """
            INSERT INTO audit_events (event_type, actor, details, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (event_type, actor, json.dumps(details, sort_keys=True), utc_now()),
        )

    @staticmethod
    def _job_select_sql(suffix: str) -> str:
        return f"""
            SELECT
                jobs.id,
                jobs.user_id,
                users.username,
                users.display_name,
                jobs.printer_id,
                printers.name AS printer_name,
                jobs.title,
                jobs.pages,
                jobs.copies,
                jobs.color,
                jobs.duplex,
                jobs.charged_pages,
                jobs.estimated_sheets,
                jobs.status,
                jobs.reason,
                jobs.created_at,
                jobs.updated_at
            FROM print_jobs AS jobs
            JOIN users ON users.id = jobs.user_id
            JOIN printers ON printers.id = jobs.printer_id
            {suffix}
        """


class ApiError(Exception):
    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        super().__init__(message)
        self.status = status


def create_handler(store: PrintManagementStore) -> type[BaseHTTPRequestHandler]:
    class PrintManagementHandler(BaseHTTPRequestHandler):
        server_version = "PrivatePrintManagement/0.1"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/":
                    self._send_html(render_dashboard(store))
                elif parsed.path == "/health":
                    self._send_json({"status": "ok"})
                elif parsed.path == "/api/users":
                    self._send_json({"users": store.list_users()})
                elif parsed.path == "/api/printers":
                    self._send_json({"printers": store.list_printers()})
                elif parsed.path == "/api/jobs":
                    self._send_json({"jobs": store.list_jobs()})
                else:
                    raise ApiError("not found", HTTPStatus.NOT_FOUND)
            except ApiError as exc:
                self._send_json({"error": str(exc)}, exc.status)
            except Exception as exc:  # pragma: no cover - safety net for server use.
                self._send_json(
                    {"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR
                )

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = self._read_json()
                if parsed.path == "/api/users":
                    item = store.create_user(
                        username=str(payload.get("username", "")),
                        display_name=payload.get("display_name"),
                        quota_pages=int(payload.get("quota_pages", 100)),
                    )
                    self._send_json({"user": item}, HTTPStatus.CREATED)
                elif parsed.path == "/api/printers":
                    item = store.create_printer(
                        name=str(payload.get("name", "")),
                        location=str(payload.get("location", "")),
                        supports_color=normalize_bool(
                            payload.get("supports_color", False)
                        ),
                    )
                    self._send_json({"printer": item}, HTTPStatus.CREATED)
                elif parsed.path == "/api/jobs":
                    item = store.submit_job(
                        user_id=int(payload.get("user_id")),
                        printer_id=int(payload.get("printer_id")),
                        title=str(payload.get("title", "")),
                        pages=int(payload.get("pages", 0)),
                        copies=int(payload.get("copies", 1)),
                        color=normalize_bool(payload.get("color", False)),
                        duplex=normalize_bool(payload.get("duplex", False)),
                    )
                    status = (
                        HTTPStatus.CREATED
                        if item["status"] == "queued"
                        else HTTPStatus.ACCEPTED
                    )
                    self._send_json({"job": item}, status)
                elif parsed.path.endswith("/release") and parsed.path.startswith(
                    "/api/jobs/"
                ):
                    job_id = parse_job_action(parsed.path, "release")
                    item = store.update_job_status(job_id, "released")
                    self._send_json({"job": item})
                elif parsed.path.endswith("/cancel") and parsed.path.startswith(
                    "/api/jobs/"
                ):
                    job_id = parse_job_action(parsed.path, "cancel")
                    item = store.update_job_status(job_id, "cancelled")
                    self._send_json({"job": item})
                else:
                    raise ApiError("not found", HTTPStatus.NOT_FOUND)
            except (ValueError, TypeError) as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except LookupError as exc:
                self._send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            except ApiError as exc:
                self._send_json({"error": str(exc)}, exc.status)
            except Exception as exc:  # pragma: no cover - safety net for server use.
                self._send_json(
                    {"error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR
                )

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError as exc:
                raise ApiError("invalid JSON payload") from exc
            if not isinstance(payload, dict):
                raise ApiError("JSON payload must be an object")
            return payload

        def _send_json(
            self,
            payload: dict[str, Any],
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_html(self, html: str) -> None:
            body = html.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return PrintManagementHandler


def parse_job_action(path: str, action: str) -> int:
    parts = path.strip("/").split("/")
    if len(parts) != 4 or parts[:2] != ["api", "jobs"] or parts[3] != action:
        raise ApiError("invalid job action path", HTTPStatus.NOT_FOUND)
    return int(parts[2])


def render_dashboard(store: PrintManagementStore) -> str:
    users = store.list_users()
    printers = store.list_printers()
    jobs = store.list_jobs()
    queued_jobs = [job for job in jobs if job["status"] == "queued"]
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Private Print Management</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
    .cards {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }}
    .card {{ border: 1px solid #d1d5db; border-radius: 0.75rem; padding: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 0.6rem; text-align: left; }}
    code {{ background: #f3f4f6; padding: 0.15rem 0.35rem; border-radius: 0.25rem; }}
  </style>
</head>
<body>
  <h1>Private Print Management</h1>
  <p>Local MVP for users, printers, print queues, quotas, and release control.</p>
  <div class="cards">
    <div class="card"><strong>{len(users)}</strong><br>Users</div>
    <div class="card"><strong>{len(printers)}</strong><br>Printers</div>
    <div class="card"><strong>{len(queued_jobs)}</strong><br>Queued jobs</div>
  </div>

  <h2>Recent jobs</h2>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>User</th><th>Printer</th><th>Title</th>
        <th>Charged pages</th><th>Status</th>
      </tr>
    </thead>
    <tbody>
      {''.join(render_job_row(job) for job in jobs[:20])}
    </tbody>
  </table>

  <h2>API quick start</h2>
  <p>Create data using <code>POST /api/users</code>, <code>POST /api/printers</code>,
  and <code>POST /api/jobs</code>.</p>
</body>
</html>"""


def render_job_row(job: dict[str, Any]) -> str:
    return (
        "<tr>"
        f"<td>{job['id']}</td>"
        f"<td>{escape_html(job['username'])}</td>"
        f"<td>{escape_html(job['printer_name'])}</td>"
        f"<td>{escape_html(job['title'])}</td>"
        f"<td>{job['charged_pages']}</td>"
        f"<td>{escape_html(job['status'])}</td>"
        "</tr>"
    )


def escape_html(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def run_server(config: AppConfig) -> None:
    store = PrintManagementStore(config.db_path)
    handler = create_handler(store)
    server = ThreadingHTTPServer((config.host, config.port), handler)
    print(f"Serving private print management on http://{config.host}:{config.port}")
    print(f"SQLite database: {config.db_path}")
    server.serve_forever()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the private print management MVP")
    parser.add_argument(
        "--db",
        default="print_management.sqlite3",
        help="SQLite database path",
    )
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host")
    parser.add_argument("--port", default=8080, type=int, help="HTTP bind port")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    run_server(AppConfig(db_path=Path(args.db), host=args.host, port=args.port))


if __name__ == "__main__":
    main()

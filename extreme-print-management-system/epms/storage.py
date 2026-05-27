"""SQLite persistence and print-management workflows."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .core import PrintCostPolicy, calculate_job_cost, evaluate_quota, money_to_cents


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def init_schema(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    department TEXT NOT NULL DEFAULT 'General',
                    balance_cents INTEGER NOT NULL DEFAULT 0,
                    monthly_quota_cents INTEGER NOT NULL DEFAULT 0,
                    overdraft_cents INTEGER NOT NULL DEFAULT 0,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS printers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    location TEXT NOT NULL DEFAULT '',
                    color_supported INTEGER NOT NULL DEFAULT 1,
                    duplex_supported INTEGER NOT NULL DEFAULT 1,
                    bw_page_cents INTEGER NOT NULL DEFAULT 5,
                    color_page_cents INTEGER NOT NULL DEFAULT 25,
                    status TEXT NOT NULL DEFAULT 'online',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS print_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    printer_id INTEGER NOT NULL REFERENCES printers(id),
                    document_name TEXT NOT NULL,
                    pages INTEGER NOT NULL,
                    copies INTEGER NOT NULL,
                    color INTEGER NOT NULL,
                    duplex INTEGER NOT NULL,
                    account TEXT NOT NULL DEFAULT 'Personal',
                    cost_cents INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    reason TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(printer_id) REFERENCES printers(id)
                );

                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    job_id INTEGER REFERENCES print_jobs(id),
                    amount_cents INTEGER NOT NULL,
                    balance_after_cents INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def seed_demo(self) -> None:
        with self.connect() as db:
            user_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            printer_count = db.execute("SELECT COUNT(*) FROM printers").fetchone()[0]
            if user_count == 0:
                db.executemany(
                    """
                    INSERT INTO users
                        (username, display_name, department, balance_cents, monthly_quota_cents, overdraft_cents)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        ("ahmed", "Ahmed Admin", "Administration", money_to_cents("25.00"), money_to_cents("25.00"), money_to_cents("5.00")),
                        ("sara", "Sara Student", "Students", money_to_cents("10.00"), money_to_cents("10.00"), money_to_cents("0.00")),
                        ("itdesk", "IT Desk", "IT", money_to_cents("50.00"), money_to_cents("50.00"), money_to_cents("20.00")),
                    ],
                )
            if printer_count == 0:
                db.executemany(
                    """
                    INSERT INTO printers
                        (name, location, color_supported, duplex_supported, bw_page_cents, color_page_cents, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        ("Main Office HP", "First floor", 1, 1, 5, 30, "online"),
                        ("Library BW", "Library", 0, 1, 3, 0, "online"),
                        ("Finance Color", "Finance room", 1, 0, 6, 35, "online"),
                    ],
                )

    def list_users(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM users ORDER BY display_name")

    def list_printers(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM printers ORDER BY name")

    def list_jobs(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT j.*, u.display_name AS user_name, p.name AS printer_name
            FROM print_jobs j
            JOIN users u ON u.id = j.user_id
            JOIN printers p ON p.id = j.printer_id
            ORDER BY j.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def add_credit(self, user_id: int, amount_cents: int, note: str = "Manual credit") -> dict[str, Any]:
        if amount_cents <= 0:
            raise ValueError("credit amount must be greater than zero")
        with self.connect() as db:
            user = self._get_row(db, "SELECT * FROM users WHERE id = ?", (user_id,))
            balance_after = user["balance_cents"] + amount_cents
            db.execute("UPDATE users SET balance_cents = ? WHERE id = ?", (balance_after, user_id))
            db.execute(
                """
                INSERT INTO transactions (user_id, amount_cents, balance_after_cents, type, note)
                VALUES (?, ?, ?, 'credit', ?)
                """,
                (user_id, amount_cents, balance_after, note),
            )
            return self._row_to_dict(self._get_row(db, "SELECT * FROM users WHERE id = ?", (user_id,)))

    def submit_job(
        self,
        *,
        user_id: int,
        printer_id: int,
        document_name: str,
        pages: int,
        copies: int,
        color: bool,
        duplex: bool,
        account: str = "Personal",
    ) -> dict[str, Any]:
        document_name = document_name.strip() or "Untitled document"
        account = account.strip() or "Personal"

        with self.connect() as db:
            user = self._get_row(db, "SELECT * FROM users WHERE id = ?", (user_id,))
            printer = self._get_row(db, "SELECT * FROM printers WHERE id = ?", (printer_id,))
            cost = calculate_job_cost(
                pages=pages,
                copies=copies,
                color=color,
                duplex=duplex,
                policy=PrintCostPolicy(
                    bw_page_cents=printer["bw_page_cents"],
                    color_page_cents=printer["color_page_cents"],
                ),
            )

            status = "printed"
            reason = "Printed and charged"
            if not user["is_active"]:
                status = "denied"
                reason = "User account is disabled"
            elif printer["status"] != "online":
                status = "held"
                reason = "Printer is not online"
            elif color and not printer["color_supported"]:
                status = "denied"
                reason = "Selected printer does not support color"
            elif duplex and not printer["duplex_supported"]:
                status = "denied"
                reason = "Selected printer does not support duplex"
            else:
                decision = evaluate_quota(
                    balance_cents=user["balance_cents"],
                    overdraft_cents=user["overdraft_cents"],
                    cost_cents=cost,
                )
                if not decision.allowed:
                    status = "held"
                    reason = decision.reason

            completed_at = "CURRENT_TIMESTAMP" if status == "printed" else "NULL"
            cursor = db.execute(
                f"""
                INSERT INTO print_jobs
                    (user_id, printer_id, document_name, pages, copies, color, duplex, account,
                     cost_cents, status, reason, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {completed_at})
                """,
                (
                    user_id,
                    printer_id,
                    document_name,
                    pages,
                    copies,
                    int(color),
                    int(duplex),
                    account,
                    cost,
                    status,
                    reason,
                ),
            )
            job_id = cursor.lastrowid
            if status == "printed":
                self._charge_job(db, user_id=user_id, job_id=job_id, cost_cents=cost)
            return self._row_to_dict(self._get_job_row(db, job_id))

    def release_job(self, job_id: int) -> dict[str, Any]:
        with self.connect() as db:
            job = self._get_job_row(db, job_id)
            if job["status"] != "held":
                raise ValueError("only held jobs can be released")
            user = self._get_row(db, "SELECT * FROM users WHERE id = ?", (job["user_id"],))
            decision = evaluate_quota(
                balance_cents=user["balance_cents"],
                overdraft_cents=user["overdraft_cents"],
                cost_cents=job["cost_cents"],
            )
            if not decision.allowed:
                raise ValueError(decision.reason)
            self._charge_job(db, user_id=job["user_id"], job_id=job_id, cost_cents=job["cost_cents"])
            db.execute(
                """
                UPDATE print_jobs
                SET status = 'printed', reason = 'Released by administrator', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (job_id,),
            )
            return self._row_to_dict(self._get_job_row(db, job_id))

    def deny_job(self, job_id: int, reason: str = "Denied by administrator") -> dict[str, Any]:
        with self.connect() as db:
            job = self._get_job_row(db, job_id)
            if job["status"] != "held":
                raise ValueError("only held jobs can be denied")
            db.execute(
                "UPDATE print_jobs SET status = 'denied', reason = ? WHERE id = ?",
                (reason, job_id),
            )
            return self._row_to_dict(self._get_job_row(db, job_id))

    def reset_monthly_quotas(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            users = db.execute("SELECT * FROM users WHERE is_active = 1").fetchall()
            for user in users:
                db.execute(
                    "UPDATE users SET balance_cents = monthly_quota_cents WHERE id = ?",
                    (user["id"],),
                )
                db.execute(
                    """
                    INSERT INTO transactions (user_id, amount_cents, balance_after_cents, type, note)
                    VALUES (?, ?, ?, 'quota_reset', 'Monthly quota reset')
                    """,
                    (user["id"], user["monthly_quota_cents"], user["monthly_quota_cents"]),
                )
            return self.list_users()

    def dashboard(self) -> dict[str, Any]:
        with self.connect() as db:
            totals = self._row_to_dict(
                db.execute(
                    """
                    SELECT
                        COUNT(*) AS jobs,
                        COALESCE(SUM(CASE WHEN status = 'printed' THEN cost_cents ELSE 0 END), 0) AS charged_cents,
                        COALESCE(SUM(CASE WHEN status = 'held' THEN 1 ELSE 0 END), 0) AS held_jobs,
                        COALESCE(SUM(pages * copies), 0) AS pages
                    FROM print_jobs
                    """
                ).fetchone()
            )
            totals["users"] = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            totals["printers"] = db.execute("SELECT COUNT(*) FROM printers").fetchone()[0]
            totals["by_user"] = self._fetch_all(
                """
                SELECT u.display_name, COUNT(j.id) AS jobs, COALESCE(SUM(j.cost_cents), 0) AS cost_cents
                FROM users u
                LEFT JOIN print_jobs j ON j.user_id = u.id AND j.status = 'printed'
                GROUP BY u.id
                ORDER BY cost_cents DESC
                LIMIT 10
                """
            )
            totals["by_printer"] = self._fetch_all(
                """
                SELECT p.name, COUNT(j.id) AS jobs, COALESCE(SUM(j.pages * j.copies), 0) AS pages
                FROM printers p
                LEFT JOIN print_jobs j ON j.printer_id = p.id AND j.status = 'printed'
                GROUP BY p.id
                ORDER BY pages DESC
                LIMIT 10
                """
            )
            return totals

    def _charge_job(self, db: sqlite3.Connection, *, user_id: int, job_id: int, cost_cents: int) -> None:
        user = self._get_row(db, "SELECT * FROM users WHERE id = ?", (user_id,))
        balance_after = user["balance_cents"] - cost_cents
        db.execute("UPDATE users SET balance_cents = ? WHERE id = ?", (balance_after, user_id))
        db.execute(
            """
            INSERT INTO transactions (user_id, job_id, amount_cents, balance_after_cents, type, note)
            VALUES (?, ?, ?, ?, 'debit', 'Print job charge')
            """,
            (user_id, job_id, -cost_cents, balance_after),
        )

    def _get_job_row(self, db: sqlite3.Connection, job_id: int) -> sqlite3.Row:
        return self._get_row(
            db,
            """
            SELECT j.*, u.display_name AS user_name, p.name AS printer_name
            FROM print_jobs j
            JOIN users u ON u.id = j.user_id
            JOIN printers p ON p.id = j.printer_id
            WHERE j.id = ?
            """,
            (job_id,),
        )

    def _fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [self._row_to_dict(row) for row in db.execute(sql, params).fetchall()]

    @staticmethod
    def _get_row(db: sqlite3.Connection, sql: str, params: tuple[Any, ...]) -> sqlite3.Row:
        row = db.execute(sql, params).fetchone()
        if row is None:
            raise ValueError("record not found")
        return row

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {key: row[key] for key in row.keys()}

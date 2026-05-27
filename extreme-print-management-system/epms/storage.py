"""SQLite persistence and print-management workflows."""

from __future__ import annotations

import json
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
                    source TEXT NOT NULL DEFAULT 'web',
                    agent_id TEXT NOT NULL DEFAULT '',
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

                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL UNIQUE,
                    agent_type TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    os_name TEXT NOT NULL DEFAULT '',
                    version TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL DEFAULT '',
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            self._ensure_column(db, "print_jobs", "source", "TEXT NOT NULL DEFAULT 'web'")
            self._ensure_column(db, "print_jobs", "agent_id", "TEXT NOT NULL DEFAULT ''")

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

    def seed_enterprise_demo(self) -> dict[str, Any]:
        """Reset the database to a polished enterprise demo scenario."""
        with self.connect() as db:
            db.execute("DELETE FROM transactions")
            db.execute("DELETE FROM print_jobs")
            db.execute("DELETE FROM agents")
            db.execute("DELETE FROM audit_logs")
            db.execute("DELETE FROM printers")
            db.execute("DELETE FROM users")
            db.execute("DELETE FROM sqlite_sequence WHERE name IN ('transactions', 'print_jobs', 'agents', 'audit_logs', 'printers', 'users')")

            db.executemany(
                """
                INSERT INTO users
                    (username, display_name, department, balance_cents, monthly_quota_cents, overdraft_cents)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    ("admin", "Nora Al-Fayed", "Executive Office", money_to_cents("150.00"), money_to_cents("150.00"), money_to_cents("50.00")),
                    ("finance", "Omar Finance", "Finance", money_to_cents("95.00"), money_to_cents("120.00"), money_to_cents("20.00")),
                    ("hr", "Lina HR", "Human Resources", money_to_cents("62.50"), money_to_cents("75.00"), money_to_cents("10.00")),
                    ("student-a", "Sara Student", "Students", money_to_cents("8.20"), money_to_cents("15.00"), money_to_cents("0.00")),
                    ("marketing", "Yousef Marketing", "Marketing", money_to_cents("44.00"), money_to_cents("60.00"), money_to_cents("15.00")),
                    ("itdesk", "Ahmed IT Desk", "IT Operations", money_to_cents("220.00"), money_to_cents("220.00"), money_to_cents("75.00")),
                ],
            )
            db.executemany(
                """
                INSERT INTO printers
                    (name, location, color_supported, duplex_supported, bw_page_cents, color_page_cents, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("HQ SecurePrint Cluster", "HQ - Level 21", 1, 1, 4, 28, "online"),
                    ("Finance Canon MEAP", "Finance Vault", 1, 1, 5, 32, "online"),
                    ("Library BW Fleet", "Public Library", 0, 1, 2, 0, "online"),
                    ("Marketing Xerox Color", "Creative Studio", 1, 1, 6, 38, "online"),
                    ("Branch HP OXP Gateway", "Remote Branch", 1, 1, 4, 30, "online"),
                    ("Archive Kyocera HyPAS", "Records Room", 0, 1, 3, 0, "maintenance"),
                ],
            )
            db.executemany(
                """
                INSERT INTO agents (agent_id, agent_type, hostname, os_name, version, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    ("server-primary-hq", "server", "epms-hq-01", "Linux 6.x", "0.1.0", '{"role": "application-server", "region": "HQ"}'),
                    ("client-agent-vdi-pool", "client", "vdi-pool-7", "Windows 11 Enterprise", "0.1.0", '{"direct_print_monitor": true, "fleet": "managed-workstations"}'),
                    ("print-provider-hq-cups", "print-provider", "cups-hq-01", "Ubuntu LTS", "0.1.0", '{"spooler": "cups", "queues": ["HQ SecurePrint Cluster", "Library BW Fleet"]}'),
                    ("printer-controller-canon-finance", "printer-controller", "canon-meap-fin-01", "Canon MEAP", "0.1.0", '{"vendor": "canon", "platform": "MEAP", "embedded": true}'),
                    ("printer-controller-hp-branch", "printer-controller", "hp-oxp-branch-02", "HP FutureSmart", "0.1.0", '{"vendor": "hp", "platform": "OXP / Workpath", "embedded": true}'),
                    ("site-server-branch-east", "site-server", "branch-east-cache", "Linux 6.x", "0.1.0", '{"offline_cache": true, "sync_mode": "planned"}'),
                ],
            )

        users = {row["username"]: row["id"] for row in self.list_users()}
        printers = {row["name"]: row["id"] for row in self.list_printers()}
        demo_jobs = [
            ("finance", "Finance Canon MEAP", "Quarterly board pack.pdf", 42, 2, True, True, "Finance", "print-provider", "print-provider-hq-cups"),
            ("admin", "HQ SecurePrint Cluster", "Executive contract bundle.pdf", 18, 1, False, True, "Executive Office", "printer-controller", "printer-controller-canon-finance"),
            ("marketing", "Marketing Xerox Color", "Campaign pitch deck.pdf", 28, 3, True, True, "Marketing", "client-agent", "client-agent-vdi-pool"),
            ("student-a", "Library BW Fleet", "Research notes.pdf", 16, 1, False, True, "Students", "client-agent", "client-agent-vdi-pool"),
            ("student-a", "HQ SecurePrint Cluster", "Full color thesis draft.pdf", 140, 1, True, True, "Students", "print-provider", "print-provider-hq-cups"),
            ("hr", "Archive Kyocera HyPAS", "Policy archive.pdf", 80, 1, False, True, "Human Resources", "print-provider", "print-provider-hq-cups"),
            ("itdesk", "Branch HP OXP Gateway", "Branch audit packet.pdf", 65, 1, True, True, "IT Operations", "site-server", "site-server-branch-east"),
        ]
        for username, printer_name, document, pages, copies, color, duplex, account, source, agent_id in demo_jobs:
            self.submit_job(
                user_id=users[username],
                printer_id=printers[printer_name],
                document_name=document,
                pages=pages,
                copies=copies,
                color=color,
                duplex=duplex,
                account=account,
                source=source,
                agent_id=agent_id,
            )
        return self.dashboard()

    def list_users(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM users ORDER BY display_name")

    def list_printers(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM printers ORDER BY name")

    def list_agents(self) -> list[dict[str, Any]]:
        agents = self._fetch_all("SELECT * FROM agents ORDER BY last_seen DESC")
        for agent in agents:
            agent["metadata"] = json.loads(agent.pop("metadata_json") or "{}")
        return agents

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
            self._insert_audit(
                db,
                actor="administrator",
                event_type="credit_added",
                entity_type="user",
                entity_id=str(user_id),
                details={"amount_cents": amount_cents, "balance_after_cents": balance_after, "note": note},
            )
            return self._row_to_dict(self._get_row(db, "SELECT * FROM users WHERE id = ?", (user_id,)))

    def record_agent_heartbeat(
        self,
        *,
        agent_id: str,
        agent_type: str,
        hostname: str,
        os_name: str = "",
        version: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        agent_id = agent_id.strip()
        agent_type = agent_type.strip()
        hostname = hostname.strip()
        if not agent_id:
            raise ValueError("agent_id is required")
        if not agent_type:
            raise ValueError("agent_type is required")
        if not hostname:
            raise ValueError("hostname is required")

        metadata_json = json.dumps(metadata or {}, sort_keys=True)
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO agents (agent_id, agent_type, hostname, os_name, version, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    agent_type = excluded.agent_type,
                    hostname = excluded.hostname,
                    os_name = excluded.os_name,
                    version = excluded.version,
                    metadata_json = excluded.metadata_json,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (agent_id, agent_type, hostname, os_name, version, metadata_json),
            )
            agent = self._row_to_dict(self._get_row(db, "SELECT * FROM agents WHERE agent_id = ?", (agent_id,)))
            agent["metadata"] = json.loads(agent.pop("metadata_json") or "{}")
            self._insert_audit(
                db,
                actor=agent_id,
                event_type="agent_heartbeat",
                entity_type="agent",
                entity_id=agent_id,
                details={"agent_type": agent_type, "hostname": hostname},
            )
            return agent

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
        source: str = "web",
        agent_id: str = "",
    ) -> dict[str, Any]:
        document_name = document_name.strip() or "Untitled document"
        account = account.strip() or "Personal"
        source = source.strip() or "web"
        agent_id = agent_id.strip()

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
                     cost_cents, status, reason, source, agent_id, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, {completed_at})
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
                    source,
                    agent_id,
                ),
            )
            job_id = cursor.lastrowid
            if status == "printed":
                self._charge_job(db, user_id=user_id, job_id=job_id, cost_cents=cost)
            self._insert_audit(
                db,
                actor=agent_id or "web",
                event_type="print_job_submitted",
                entity_type="print_job",
                entity_id=str(job_id),
                details={"status": status, "source": source, "cost_cents": cost},
            )
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
            self._insert_audit(
                db,
                actor="administrator",
                event_type="print_job_released",
                entity_type="print_job",
                entity_id=str(job_id),
                details={"cost_cents": job["cost_cents"]},
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
            self._insert_audit(
                db,
                actor="administrator",
                event_type="print_job_denied",
                entity_type="print_job",
                entity_id=str(job_id),
                details={"reason": reason},
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
            self._insert_audit(
                db,
                actor="administrator",
                event_type="quota_reset",
                entity_type="user",
                entity_id="all_active",
                details={"active_users": len(users)},
            )
            return self.list_users()

    def list_audit_logs(self, limit: int = 100) -> list[dict[str, Any]]:
        logs = self._fetch_all(
            """
            SELECT * FROM audit_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        for log in logs:
            log["details"] = json.loads(log.pop("details_json") or "{}")
        return logs

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
            totals["agents"] = db.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            totals["audit_logs"] = db.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
            totals["denied_jobs"] = db.execute("SELECT COUNT(*) FROM print_jobs WHERE status = 'denied'").fetchone()[0]
            totals["printed_jobs"] = db.execute("SELECT COUNT(*) FROM print_jobs WHERE status = 'printed'").fetchone()[0]
            totals["estimated_savings_cents"] = int(totals["pages"] or 0) * 2
            totals["readiness"] = {
                "server": True,
                "client_agent": db.execute("SELECT COUNT(*) FROM agents WHERE agent_type = 'client'").fetchone()[0] > 0,
                "print_provider": db.execute("SELECT COUNT(*) FROM agents WHERE agent_type = 'print-provider'").fetchone()[0] > 0,
                "printer_controller": db.execute("SELECT COUNT(*) FROM agents WHERE agent_type = 'printer-controller'").fetchone()[0] > 0,
                "site_server_planned": True,
            }
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
            totals["by_source"] = self._fetch_all(
                """
                SELECT source, COUNT(*) AS jobs, COALESCE(SUM(cost_cents), 0) AS cost_cents
                FROM print_jobs
                GROUP BY source
                ORDER BY jobs DESC
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

    @staticmethod
    def _insert_audit(
        db: sqlite3.Connection,
        *,
        actor: str,
        event_type: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, Any],
    ) -> None:
        db.execute(
            """
            INSERT INTO audit_logs (actor, event_type, entity_type, entity_id, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (actor, event_type, entity_type, entity_id, json.dumps(details, sort_keys=True)),
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

    @staticmethod
    def _ensure_column(db: sqlite3.Connection, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in columns:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

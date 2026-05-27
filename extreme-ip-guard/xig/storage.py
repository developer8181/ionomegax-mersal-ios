"""SQLite persistence layer for Extreme IP Guard.

This module is the single owner of the database schema and is the only place
that mutates persistent state. Every component that writes to the database
goes through one of the explicit methods here; this keeps the audit chain
correct (rows can only be inserted through paths that update the chain).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable

from .audit import AuditChain
from .core import (
    Severity,
    TelemetryEvent,
    blend_risk,
    classify_risk,
    severity_at_least,
    utc_now_iso,
)
from .crypto import AgentKeyPair, hash_password, random_token, verify_password
from .detection import Alert, DetectionEngine
from .policies import (
    PolicyBundle,
    Rule,
    default_iocs,
    default_playbooks,
    default_rules,
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'analyst',
    department TEXT NOT NULL DEFAULT 'General',
    password_json TEXT NOT NULL DEFAULT '{}',
    risk_score REAL NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hostname TEXT NOT NULL UNIQUE,
    os_name TEXT NOT NULL DEFAULT '',
    hw_fp TEXT NOT NULL DEFAULT '',
    owner_user_id INTEGER REFERENCES users(id),
    criticality TEXT NOT NULL DEFAULT 'normal',
    tags TEXT NOT NULL DEFAULT '[]',
    risk_score REAL NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL UNIQUE,
    asset_id INTEGER REFERENCES assets(id),
    version TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    public_key TEXT NOT NULL DEFAULT '',
    secret_b64 TEXT NOT NULL DEFAULT '',
    enrol_token TEXT NOT NULL DEFAULT '',
    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL,
    issued_at TEXT NOT NULL,
    body_json TEXT NOT NULL,
    signature TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    kind TEXT NOT NULL,
    ts TEXT NOT NULL,
    subject TEXT NOT NULL DEFAULT '',
    data_json TEXT NOT NULL DEFAULT '{}',
    risk_delta REAL NOT NULL DEFAULT 0,
    prev_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_events_agent ON events(agent_id);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);

CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_uid TEXT NOT NULL UNIQUE,
    ts TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    mitre TEXT NOT NULL DEFAULT '',
    agent_id TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    event_kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    response TEXT NOT NULL DEFAULT 'alert_only',
    risk_delta REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'new',
    data_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_uid TEXT NOT NULL UNIQUE,
    agent_id TEXT NOT NULL,
    playbook TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    signature TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'queued',
    result_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_commands_agent_status ON commands(agent_id, status);

CREATE TABLE IF NOT EXISTS audit_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target TEXT NOT NULL DEFAULT '',
    data_json TEXT NOT NULL DEFAULT '{}',
    prev_hash TEXT NOT NULL,
    chain_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chain_state (
    name TEXT PRIMARY KEY,
    last_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ioc_indicators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'manual',
    added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kind, value)
);
"""


class Database:
    """SQLite-backed storage with a tamper-evident audit chain."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.RLock()
        self._engine = DetectionEngine(rules=default_rules(), iocs=default_iocs())

    # ---- connection helpers ----

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def init_schema(self) -> None:
        with self._lock, self.connect() as db:
            db.executescript(SCHEMA)
            self._ensure_chain(db, "events")
            self._ensure_chain(db, "audit")

    def seed_demo(self) -> None:
        with self._lock, self.connect() as db:
            count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            if count == 0:
                db.executemany(
                    """
                    INSERT INTO users (username, display_name, role, department, password_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        ("admin", "Console Admin", "admin", "SOC", json.dumps(hash_password("admin"))),
                        ("analyst", "Security Analyst", "analyst", "SOC", json.dumps(hash_password("analyst"))),
                        ("auditor", "Compliance Auditor", "auditor", "Risk", json.dumps(hash_password("auditor"))),
                        ("sara", "Sara from Finance", "viewer", "Finance", json.dumps(hash_password("sara"))),
                    ],
                )
            count = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            if count == 0:
                db.executemany(
                    """
                    INSERT INTO assets (hostname, os_name, hw_fp, criticality, tags)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        ("WS-ADMIN-01", "Windows 11", "win-hwfp-001", "high", json.dumps(["admin", "finance"])),
                        ("MBP-ANALYST-01", "macOS 14", "mac-hwfp-002", "normal", json.dumps(["soc"])),
                        ("UB-DEV-01", "Ubuntu 24.04", "linux-hwfp-003", "normal", json.dumps(["dev"])),
                    ],
                )
            count = db.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
            if count == 0:
                self.publish_default_policy(db, actor="system:bootstrap")
            self._engine.load(rules=self._load_rules(db), iocs=self._load_iocs(db))

    # ---- detection engine accessor ----

    @property
    def engine(self) -> DetectionEngine:
        return self._engine

    # ---- listings used by the API ----

    def list_users(self) -> list[dict[str, Any]]:
        rows = self._fetch_all("SELECT id, username, display_name, role, department, risk_score, is_active FROM users ORDER BY display_name")
        for row in rows:
            row["risk_band"] = classify_risk(row["risk_score"]).value
        return rows

    def list_assets(self) -> list[dict[str, Any]]:
        rows = self._fetch_all("SELECT * FROM assets ORDER BY hostname")
        for row in rows:
            row["tags"] = json.loads(row.pop("tags") or "[]")
            row["risk_band"] = classify_risk(row["risk_score"]).value
        return rows

    def list_agents(self) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT a.id, a.agent_id, a.asset_id, a.version, a.status, a.last_seen, a.created_at,
                   COALESCE(s.hostname, '') AS hostname, COALESCE(s.os_name, '') AS os_name,
                   COALESCE(s.risk_score, 0) AS risk_score
            FROM agents a
            LEFT JOIN assets s ON s.id = a.asset_id
            ORDER BY a.last_seen DESC
            """
        )
        for row in rows:
            row["risk_band"] = classify_risk(row["risk_score"]).value
        return rows

    def list_alerts(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            """
            SELECT a.*, COALESCE(u.display_name, '') AS user_name
            FROM alerts a
            LEFT JOIN users u ON u.id = a.user_id
            ORDER BY a.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        for row in rows:
            row["data"] = json.loads(row.pop("data_json") or "{}")
        return rows

    def list_events(self, limit: int = 200) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            "SELECT id, agent_id, user_id, kind, ts, subject, data_json, risk_delta, chain_hash FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        for row in rows:
            row["data"] = json.loads(row.pop("data_json") or "{}")
        return rows

    def list_commands(self, agent_id: str | None = None, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        sql = "SELECT * FROM commands"
        params: list[Any] = []
        clauses: list[str] = []
        if agent_id:
            clauses.append("agent_id = ?")
            params.append(agent_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = self._fetch_all(sql, tuple(params))
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json") or "{}")
            row["result"] = json.loads(row.pop("result_json") or "{}")
        return rows

    def list_audit_entries(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._fetch_all(
            "SELECT * FROM audit_entries ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        for row in rows:
            row["data"] = json.loads(row.pop("data_json") or "{}")
        return rows

    def list_iocs(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM ioc_indicators ORDER BY id DESC LIMIT 500")

    def list_policies(self) -> list[dict[str, Any]]:
        rows = self._fetch_all("SELECT id, version, issued_at, signature FROM policies ORDER BY version DESC LIMIT 50")
        return rows

    # ---- agent lifecycle ----

    def issue_enrol_token(self, *, hostname: str, criticality: str = "normal", actor: str = "console") -> dict[str, Any]:
        token = random_token()
        with self._lock, self.connect() as db:
            asset = db.execute("SELECT id FROM assets WHERE hostname = ?", (hostname,)).fetchone()
            if asset is None:
                cursor = db.execute(
                    "INSERT INTO assets (hostname, criticality) VALUES (?, ?)",
                    (hostname, criticality),
                )
                asset_id = cursor.lastrowid
            else:
                asset_id = asset["id"]
            db.execute(
                "INSERT INTO agents (agent_id, asset_id, status, enrol_token) VALUES (?, ?, 'pending', ?)",
                (f"pending-{token[:8]}", asset_id, token),
            )
            self._record_audit(
                db,
                actor=actor,
                action="agent.enrol_token.issued",
                target=hostname,
                data={"asset_id": asset_id, "token_prefix": token[:8]},
            )
        return {"hostname": hostname, "enrol_token": token}

    def enrol_agent(self, *, enrol_token: str, agent_id: str, hw_fp: str, os_name: str, version: str) -> dict[str, Any]:
        if not enrol_token or not agent_id:
            raise ValueError("enrol_token and agent_id are required")
        with self._lock, self.connect() as db:
            pending = db.execute(
                "SELECT * FROM agents WHERE enrol_token = ? AND status = 'pending'",
                (enrol_token,),
            ).fetchone()
            if pending is None:
                raise ValueError("invalid or already-used enrolment token")
            keypair = AgentKeyPair.generate(agent_id)
            db.execute(
                """
                UPDATE agents
                SET agent_id = ?, version = ?, status = 'active',
                    public_key = ?, secret_b64 = ?, enrol_token = '', last_seen = ?
                WHERE id = ?
                """,
                (
                    agent_id,
                    version,
                    keypair.public_key,
                    keypair.secret,
                    utc_now_iso(),
                    pending["id"],
                ),
            )
            db.execute(
                "UPDATE assets SET hw_fp = ?, os_name = ? WHERE id = ?",
                (hw_fp, os_name, pending["asset_id"]),
            )
            self._record_audit(
                db,
                actor=f"agent:{agent_id}",
                action="agent.enrolled",
                target=agent_id,
                data={"asset_id": pending["asset_id"], "os": os_name, "version": version},
            )
            bundle = self._current_bundle(db)
        return {
            "agent_id": agent_id,
            "agent_secret": keypair.secret,
            "policy_bundle": bundle.to_dict(),
        }

    def record_heartbeat(self, *, agent_id: str, version: str = "") -> dict[str, Any]:
        with self._lock, self.connect() as db:
            row = db.execute("SELECT * FROM agents WHERE agent_id = ? AND status = 'active'", (agent_id,)).fetchone()
            if row is None:
                raise ValueError("unknown or inactive agent")
            db.execute(
                "UPDATE agents SET last_seen = ?, version = COALESCE(NULLIF(?, ''), version) WHERE id = ?",
                (utc_now_iso(), version, row["id"]),
            )
            bundle_version = db.execute("SELECT COALESCE(MAX(version), 0) FROM policies").fetchone()[0]
        return {"agent_id": agent_id, "policy_version": bundle_version}

    # ---- telemetry ingestion ----

    def ingest_event(self, event: TelemetryEvent, *, user_id: int | None = None) -> dict[str, Any]:
        event.validate()
        with self._lock, self.connect() as db:
            chain = self._chain(db, "events")
            record = chain.append(
                {
                    "agent_id": event.agent_id,
                    "kind": event.kind,
                    "ts": event.ts,
                    "subject": event.subject,
                    "data": event.data,
                }
            )
            alerts, updates = self._engine.evaluate(event, user_id=str(user_id or ""))
            risk_delta_total = sum(alert.risk_delta for alert in alerts)
            db.execute(
                """
                INSERT INTO events (agent_id, user_id, kind, ts, subject, data_json, risk_delta, prev_hash, chain_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.agent_id,
                    user_id,
                    event.kind,
                    event.ts,
                    event.subject,
                    json.dumps(event.data, sort_keys=True),
                    risk_delta_total,
                    record.prev_hash,
                    record.chain_hash,
                ),
            )
            self._save_chain(db, "events", chain.last_hash)
            for update in updates:
                self._apply_risk(db, update.subject_kind, update.subject_id, update.delta)
            stored_alerts = [self._persist_alert(db, alert, user_id=user_id) for alert in alerts]
            queued_commands = [self._queue_response(db, alert) for alert in alerts if alert.response not in {"", "alert_only"}]
        return {
            "chain_hash": record.chain_hash,
            "alerts": stored_alerts,
            "commands_queued": [cmd for cmd in queued_commands if cmd is not None],
        }

    # ---- policy publication ----

    def publish_default_policy(self, db: sqlite3.Connection | None = None, *, actor: str = "console") -> dict[str, Any]:
        own_conn = db is None
        if own_conn:
            db = self.connect()
        try:
            current = db.execute("SELECT COALESCE(MAX(version), 0) FROM policies").fetchone()[0]
            version = int(current) + 1
            bundle = PolicyBundle(
                version=version,
                rules=default_rules(),
                iocs=default_iocs(),
                playbooks=list(default_playbooks().keys()),
                issued_at=utc_now_iso(),
                signature="",
            )
            db.execute(
                "INSERT INTO policies (version, issued_at, body_json, signature) VALUES (?, ?, ?, ?)",
                (
                    bundle.version,
                    bundle.issued_at,
                    json.dumps(bundle.to_dict(), sort_keys=True),
                    bundle.signature,
                ),
            )
            for kind, values in bundle.iocs.items():
                for value in values:
                    db.execute(
                        "INSERT OR IGNORE INTO ioc_indicators (kind, value, source) VALUES (?, ?, 'bootstrap')",
                        (kind, value),
                    )
            self._record_audit(
                db,
                actor=actor,
                action="policy.published",
                target=f"v{version}",
                data={"rules": [rule.id for rule in bundle.rules], "iocs": bundle.iocs},
            )
            return bundle.to_dict()
        finally:
            if own_conn:
                db.close()

    def add_ioc(self, *, kind: str, value: str, source: str = "console", actor: str = "console") -> dict[str, Any]:
        kind = (kind or "").strip().lower()
        value = (value or "").strip().lower()
        if kind not in {"sha256", "domain", "ipv4", "ipv6", "ja3"}:
            raise ValueError("unsupported ioc kind")
        if not value:
            raise ValueError("ioc value is required")
        with self._lock, self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO ioc_indicators (kind, value, source) VALUES (?, ?, ?)",
                (kind, value, source),
            )
            self._record_audit(
                db,
                actor=actor,
                action="ioc.added",
                target=f"{kind}:{value}",
                data={"source": source},
            )
            self._engine.add_ioc(kind, value)
        return {"kind": kind, "value": value, "source": source}

    # ---- response queue ----

    def fetch_pending_commands(self, agent_id: str) -> list[dict[str, Any]]:
        with self._lock, self.connect() as db:
            rows = db.execute(
                "SELECT * FROM commands WHERE agent_id = ? AND status = 'queued' ORDER BY id ASC",
                (agent_id,),
            ).fetchall()
            commands = [self._row_to_dict(r) for r in rows]
            for command in commands:
                command["payload"] = json.loads(command.pop("payload_json") or "{}")
                command["result"] = json.loads(command.pop("result_json") or "{}")
                db.execute(
                    "UPDATE commands SET status = 'dispatched' WHERE id = ?",
                    (command["id"],),
                )
        return commands

    def complete_command(self, *, command_uid: str, status: str, result: dict[str, Any], actor: str) -> dict[str, Any]:
        if status not in {"succeeded", "failed", "skipped"}:
            raise ValueError("invalid status")
        with self._lock, self.connect() as db:
            row = db.execute("SELECT * FROM commands WHERE command_uid = ?", (command_uid,)).fetchone()
            if row is None:
                raise ValueError("unknown command")
            db.execute(
                "UPDATE commands SET status = ?, result_json = ?, completed_at = ? WHERE id = ?",
                (status, json.dumps(result, sort_keys=True), utc_now_iso(), row["id"]),
            )
            self._record_audit(
                db,
                actor=actor,
                action="command.completed",
                target=command_uid,
                data={"status": status, "result": result},
            )
            return {"command_uid": command_uid, "status": status}

    # ---- dashboards ----

    def dashboard(self) -> dict[str, Any]:
        with self._lock, self.connect() as db:
            agents_total = db.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'").fetchone()[0]
            assets_total = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            users_total = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            events_total = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            alerts_total = db.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
            open_alerts = db.execute("SELECT COUNT(*) FROM alerts WHERE status = 'new'").fetchone()[0]
            high_alerts = db.execute(
                "SELECT COUNT(*) FROM alerts WHERE severity IN ('high', 'critical')"
            ).fetchone()[0]
            top_users = self._fetch_all(
                "SELECT display_name, department, risk_score FROM users ORDER BY risk_score DESC LIMIT 5"
            )
            top_assets = self._fetch_all(
                "SELECT hostname, criticality, risk_score FROM assets ORDER BY risk_score DESC LIMIT 5"
            )
            mitre_breakdown = self._fetch_all(
                "SELECT mitre, COUNT(*) AS hits FROM alerts WHERE mitre <> '' GROUP BY mitre ORDER BY hits DESC LIMIT 10"
            )
            latest_audit = self._fetch_all(
                "SELECT ts, actor, action, target FROM audit_entries ORDER BY id DESC LIMIT 5"
            )
        for row in top_users:
            row["risk_band"] = classify_risk(row["risk_score"]).value
        for row in top_assets:
            row["risk_band"] = classify_risk(row["risk_score"]).value
        return {
            "totals": {
                "agents": agents_total,
                "assets": assets_total,
                "users": users_total,
                "events": events_total,
                "alerts": alerts_total,
                "open_alerts": open_alerts,
                "high_alerts": high_alerts,
            },
            "top_users": top_users,
            "top_assets": top_assets,
            "mitre": mitre_breakdown,
            "audit": latest_audit,
        }

    # ---- audit chain verification ----

    def verify_event_chain(self) -> dict[str, Any]:
        rows = self._fetch_all(
            "SELECT agent_id, kind, ts, subject, data_json, prev_hash, chain_hash FROM events ORDER BY id ASC"
        )
        for row in rows:
            row["data"] = json.loads(row.pop("data_json") or "{}")
        ok, broken = AuditChain.verify(rows)
        return {"chain": "events", "intact": ok, "broken_at": broken, "count": len(rows)}

    def verify_audit_chain(self) -> dict[str, Any]:
        rows = self._fetch_all(
            "SELECT ts, actor, action, target, data_json, prev_hash, chain_hash FROM audit_entries ORDER BY id ASC"
        )
        for row in rows:
            row["data"] = json.loads(row.pop("data_json") or "{}")
        ok, broken = AuditChain.verify(rows)
        return {"chain": "audit", "intact": ok, "broken_at": broken, "count": len(rows)}

    # ---- alert workflow ----

    def update_alert_status(self, *, alert_uid: str, status: str, actor: str) -> dict[str, Any]:
        if status not in {"new", "acknowledged", "resolved", "false_positive"}:
            raise ValueError("invalid alert status")
        with self._lock, self.connect() as db:
            row = db.execute("SELECT * FROM alerts WHERE alert_uid = ?", (alert_uid,)).fetchone()
            if row is None:
                raise ValueError("unknown alert")
            db.execute("UPDATE alerts SET status = ? WHERE id = ?", (status, row["id"]))
            self._record_audit(
                db,
                actor=actor,
                action="alert.status_changed",
                target=alert_uid,
                data={"from": row["status"], "to": status},
            )
            return {"alert_uid": alert_uid, "status": status}

    # ---- authentication for console users ----

    def authenticate(self, username: str, password: str) -> dict[str, Any] | None:
        row = self._get_row_or_none("SELECT * FROM users WHERE username = ?", (username,))
        if row is None or not row["is_active"]:
            return None
        try:
            stored = json.loads(row["password_json"] or "{}")
        except json.JSONDecodeError:
            return None
        if not stored or not verify_password(password, stored):
            return None
        return {
            "id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"],
            "role": row["role"],
        }

    # ---- private helpers ----

    def _current_bundle(self, db: sqlite3.Connection) -> PolicyBundle:
        row = db.execute("SELECT * FROM policies ORDER BY version DESC LIMIT 1").fetchone()
        if row is None:
            return PolicyBundle(version=0, rules=[], issued_at=utc_now_iso())
        body = json.loads(row["body_json"])
        rules = [Rule(**rule) for rule in body.get("rules", [])]
        return PolicyBundle(
            version=int(body["version"]),
            rules=rules,
            iocs=body.get("iocs", {}),
            playbooks=body.get("playbooks", []),
            issued_at=body.get("issued_at", ""),
            signature=body.get("signature", ""),
        )

    def _load_rules(self, db: sqlite3.Connection) -> list[Rule]:
        bundle = self._current_bundle(db)
        return list(bundle.rules)

    def _load_iocs(self, db: sqlite3.Connection) -> dict[str, list[str]]:
        iocs: dict[str, list[str]] = {}
        for row in db.execute("SELECT kind, value FROM ioc_indicators").fetchall():
            iocs.setdefault(row["kind"], []).append(row["value"])
        return iocs

    def _ensure_chain(self, db: sqlite3.Connection, name: str) -> None:
        row = db.execute("SELECT last_hash FROM chain_state WHERE name = ?", (name,)).fetchone()
        if row is None:
            db.execute(
                "INSERT INTO chain_state (name, last_hash) VALUES (?, ?)",
                (name, AuditChain().last_hash),
            )

    def _chain(self, db: sqlite3.Connection, name: str) -> AuditChain:
        row = db.execute("SELECT last_hash FROM chain_state WHERE name = ?", (name,)).fetchone()
        if row is None:
            self._ensure_chain(db, name)
            return AuditChain()
        return AuditChain(last_hash=row["last_hash"])

    def _save_chain(self, db: sqlite3.Connection, name: str, last_hash: str) -> None:
        db.execute("UPDATE chain_state SET last_hash = ? WHERE name = ?", (last_hash, name))

    def _record_audit(
        self,
        db: sqlite3.Connection,
        *,
        actor: str,
        action: str,
        target: str = "",
        data: dict[str, Any] | None = None,
    ) -> None:
        ts = utc_now_iso()
        chain = self._chain(db, "audit")
        body = {"ts": ts, "actor": actor, "action": action, "target": target, "data": data or {}}
        record = chain.append(body)
        db.execute(
            """
            INSERT INTO audit_entries (ts, actor, action, target, data_json, prev_hash, chain_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ts, actor, action, target, json.dumps(data or {}, sort_keys=True), record.prev_hash, record.chain_hash),
        )
        self._save_chain(db, "audit", chain.last_hash)

    def _persist_alert(self, db: sqlite3.Connection, alert: Alert, *, user_id: int | None) -> dict[str, Any]:
        db.execute(
            """
            INSERT OR IGNORE INTO alerts
                (alert_uid, ts, severity, title, rule_id, mitre, agent_id, user_id,
                 event_kind, summary, response, risk_delta, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert.id,
                alert.ts,
                alert.severity,
                alert.title,
                alert.rule_id,
                alert.mitre,
                alert.agent_id,
                user_id,
                alert.event_kind,
                alert.summary,
                alert.response,
                alert.risk_delta,
                json.dumps(alert.data, sort_keys=True),
            ),
        )
        self._record_audit(
            db,
            actor="detection-engine",
            action="alert.raised",
            target=alert.id,
            data={"severity": alert.severity, "rule_id": alert.rule_id, "mitre": alert.mitre},
        )
        return {
            "alert_uid": alert.id,
            "severity": alert.severity,
            "title": alert.title,
            "rule_id": alert.rule_id,
            "mitre": alert.mitre,
            "response": alert.response,
        }

    def _queue_response(self, db: sqlite3.Connection, alert: Alert) -> dict[str, Any] | None:
        playbook_id = alert.response
        playbook = default_playbooks().get(playbook_id)
        if playbook is None:
            return None
        command_uid = f"CMD-{alert.id}"
        payload = {"playbook": playbook, "context": {"alert_uid": alert.id, "severity": alert.severity}}
        db.execute(
            """
            INSERT OR IGNORE INTO commands (command_uid, agent_id, playbook, payload_json, status)
            VALUES (?, ?, ?, ?, 'queued')
            """,
            (command_uid, alert.agent_id, playbook_id, json.dumps(payload, sort_keys=True)),
        )
        self._record_audit(
            db,
            actor="soar-lite",
            action="command.queued",
            target=command_uid,
            data={"playbook": playbook_id, "agent_id": alert.agent_id},
        )
        return {"command_uid": command_uid, "playbook": playbook_id, "agent_id": alert.agent_id}

    def _apply_risk(self, db: sqlite3.Connection, kind: str, subject_id: str, delta: float) -> None:
        if not subject_id:
            return
        if kind == "user":
            row = db.execute("SELECT id, risk_score FROM users WHERE id = ? OR username = ?", (subject_id, subject_id)).fetchone()
            if row is None:
                return
            blended = blend_risk(row["risk_score"], delta)
            db.execute("UPDATE users SET risk_score = ? WHERE id = ?", (blended, row["id"]))
        elif kind == "asset":
            row = db.execute(
                """
                SELECT s.id, s.risk_score FROM assets s
                JOIN agents a ON a.asset_id = s.id
                WHERE a.agent_id = ?
                """,
                (subject_id,),
            ).fetchone()
            if row is None:
                return
            blended = blend_risk(row["risk_score"], delta)
            db.execute("UPDATE assets SET risk_score = ? WHERE id = ?", (blended, row["id"]))

    # ---- low-level helpers ----

    def _fetch_all(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [self._row_to_dict(row) for row in db.execute(sql, tuple(params)).fetchall()]

    def _get_row_or_none(self, sql: str, params: Iterable[Any] = ()) -> sqlite3.Row | None:
        with self.connect() as db:
            return db.execute(sql, tuple(params)).fetchone()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {key: row[key] for key in row.keys()}


__all__ = [
    "Database",
    "severity_at_least",
]

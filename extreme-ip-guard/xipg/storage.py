"""SQLite storage and workflow orchestration for Extreme IP Guard."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .core import GuardPolicy, NetworkEvent, normalize_ip, score_event


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
                CREATE TABLE IF NOT EXISTS assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT NOT NULL UNIQUE,
                    owner TEXT NOT NULL,
                    segment TEXT NOT NULL DEFAULT 'users',
                    criticality TEXT NOT NULL DEFAULT 'medium',
                    trust_score INTEGER NOT NULL DEFAULT 100,
                    posture TEXT NOT NULL DEFAULT 'healthy',
                    last_ip TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    mode TEXT NOT NULL DEFAULT 'enforce',
                    trusted_networks_json TEXT NOT NULL DEFAULT '[]',
                    block_ports_json TEXT NOT NULL DEFAULT '[]',
                    hard_block_countries_json TEXT NOT NULL DEFAULT '[]',
                    challenge_threshold INTEGER NOT NULL DEFAULT 45,
                    block_threshold INTEGER NOT NULL DEFAULT 70,
                    quarantine_threshold INTEGER NOT NULL DEFAULT 90,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL REFERENCES assets(id),
                    source_ip TEXT NOT NULL,
                    destination_ip TEXT NOT NULL,
                    destination_port INTEGER NOT NULL,
                    protocol TEXT NOT NULL,
                    country TEXT NOT NULL,
                    bytes_out INTEGER NOT NULL DEFAULT 0,
                    bytes_in INTEGER NOT NULL DEFAULT 0,
                    process_name TEXT NOT NULL DEFAULT '',
                    ip_reputation_score INTEGER NOT NULL DEFAULT 0,
                    tor_exit_node INTEGER NOT NULL DEFAULT 0,
                    geo_anomaly INTEGER NOT NULL DEFAULT 0,
                    burst_connections INTEGER NOT NULL DEFAULT 0,
                    risk_score INTEGER NOT NULL,
                    severity TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reasons_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER NOT NULL REFERENCES assets(id),
                    event_id INTEGER NOT NULL UNIQUE REFERENCES events(id),
                    status TEXT NOT NULL DEFAULT 'open',
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resolution_note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT
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
                """
            )

    def seed_demo(self) -> None:
        with self.connect() as db:
            asset_count = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            policy_count = db.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
            if asset_count == 0:
                db.executemany(
                    """
                    INSERT INTO assets
                        (hostname, owner, segment, criticality, trust_score, posture, last_ip)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        ("finance-laptop-07", "Noura Finance", "finance", "critical", 96, "healthy", "10.10.20.17"),
                        ("soc-analyst-01", "SOC Team", "operations", "high", 92, "monitored", "10.10.30.21"),
                        ("branch-gateway-02", "Branch Office", "edge", "high", 88, "restricted", "172.16.8.2"),
                    ],
                )
            if policy_count == 0:
                db.execute(
                    """
                    INSERT INTO policies
                        (name, mode, trusted_networks_json, block_ports_json, hard_block_countries_json,
                         challenge_threshold, block_threshold, quarantine_threshold)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "Adaptive Zero-Trust Egress",
                        "enforce",
                        json.dumps(["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]),
                        json.dumps([23, 135, 139, 445, 3389]),
                        json.dumps(["KP", "IR"]),
                        45,
                        70,
                        90,
                    ),
                )

    def list_assets(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM assets ORDER BY trust_score ASC, hostname ASC")

    def list_agents(self) -> list[dict[str, Any]]:
        agents = self._fetch_all("SELECT * FROM agents ORDER BY last_seen DESC")
        for agent in agents:
            agent["metadata"] = json.loads(agent.pop("metadata_json") or "{}")
        return agents

    def list_policies(self) -> list[dict[str, Any]]:
        policies = self._fetch_all("SELECT * FROM policies ORDER BY enabled DESC, id ASC")
        for policy in policies:
            policy["trusted_networks"] = json.loads(policy.pop("trusted_networks_json") or "[]")
            policy["block_ports"] = json.loads(policy.pop("block_ports_json") or "[]")
            policy["hard_block_countries"] = json.loads(policy.pop("hard_block_countries_json") or "[]")
        return policies

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        events = self._fetch_all(
            """
            SELECT e.*, a.hostname AS asset_name, a.owner AS asset_owner
            FROM events e
            JOIN assets a ON a.id = e.asset_id
            ORDER BY e.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        for event in events:
            event["reasons"] = json.loads(event.pop("reasons_json") or "[]")
        return events

    def list_incidents(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT i.*, a.hostname AS asset_name, e.destination_ip, e.destination_port, e.process_name
            FROM incidents i
            JOIN assets a ON a.id = i.asset_id
            JOIN events e ON e.id = i.event_id
            ORDER BY CASE WHEN i.status = 'open' THEN 0 ELSE 1 END, i.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def dashboard(self) -> dict[str, Any]:
        with self.connect() as db:
            totals = self._row_to_dict(
                db.execute(
                    """
                    SELECT
                        COUNT(*) AS events,
                        COALESCE(SUM(CASE WHEN action = 'observe' THEN 1 ELSE 0 END), 0) AS observed,
                        COALESCE(SUM(CASE WHEN action = 'challenge' THEN 1 ELSE 0 END), 0) AS challenged,
                        COALESCE(SUM(CASE WHEN action = 'block' THEN 1 ELSE 0 END), 0) AS blocked,
                        COALESCE(SUM(CASE WHEN action = 'quarantine' THEN 1 ELSE 0 END), 0) AS quarantined,
                        COALESCE(ROUND(AVG(risk_score), 2), 0) AS average_risk
                    FROM events
                    """
                ).fetchone()
            )
            totals["assets"] = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            totals["open_incidents"] = db.execute("SELECT COUNT(*) FROM incidents WHERE status = 'open'").fetchone()[0]
            totals["agents"] = db.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            totals["quarantined_assets"] = db.execute(
                "SELECT COUNT(*) FROM assets WHERE posture = 'quarantined'"
            ).fetchone()[0]
            totals["top_assets"] = self._fetch_all(
                """
                SELECT a.hostname, COUNT(e.id) AS events, MAX(e.risk_score) AS max_risk
                FROM assets a
                LEFT JOIN events e ON e.asset_id = a.id
                GROUP BY a.id
                ORDER BY max_risk DESC, events DESC, a.hostname ASC
                LIMIT 10
                """
            )
            totals["top_countries"] = self._fetch_all(
                """
                SELECT country, COUNT(*) AS events,
                       SUM(CASE WHEN action IN ('block', 'quarantine') THEN 1 ELSE 0 END) AS disruptive_actions
                FROM events
                GROUP BY country
                ORDER BY disruptive_actions DESC, events DESC, country ASC
                LIMIT 10
                """
            )
            return totals

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
            return agent

    def ingest_event(
        self,
        *,
        asset_id: int,
        source_ip: str,
        destination_ip: str,
        destination_port: int,
        protocol: str,
        country: str,
        bytes_out: int = 0,
        bytes_in: int = 0,
        process_name: str = "",
        ip_reputation_score: int = 0,
        tor_exit_node: bool = False,
        geo_anomaly: bool = False,
        burst_connections: int = 0,
    ) -> dict[str, Any]:
        with self.connect() as db:
            asset = self._get_row(db, "SELECT * FROM assets WHERE id = ?", (asset_id,))
            policy = self._load_active_policy(db)
            decision = score_event(
                NetworkEvent(
                    source_ip=normalize_ip(source_ip),
                    destination_ip=normalize_ip(destination_ip),
                    destination_port=destination_port,
                    protocol=protocol.strip().lower() or "tcp",
                    country=country.strip().upper() or "ZZ",
                    bytes_out=bytes_out,
                    bytes_in=bytes_in,
                    process_name=process_name.strip(),
                    ip_reputation_score=ip_reputation_score,
                    tor_exit_node=bool(tor_exit_node),
                    geo_anomaly=bool(geo_anomaly),
                    burst_connections=burst_connections,
                    asset_criticality=str(asset["criticality"]),
                ),
                policy,
            )

            cursor = db.execute(
                """
                INSERT INTO events
                    (asset_id, source_ip, destination_ip, destination_port, protocol, country,
                     bytes_out, bytes_in, process_name, ip_reputation_score, tor_exit_node,
                     geo_anomaly, burst_connections, risk_score, severity, action, reasons_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset_id,
                    normalize_ip(source_ip),
                    normalize_ip(destination_ip),
                    destination_port,
                    protocol.strip().lower() or "tcp",
                    country.strip().upper() or "ZZ",
                    bytes_out,
                    bytes_in,
                    process_name.strip(),
                    ip_reputation_score,
                    int(bool(tor_exit_node)),
                    int(bool(geo_anomaly)),
                    burst_connections,
                    decision.risk_score,
                    decision.severity,
                    decision.action,
                    json.dumps(list(decision.reasons)),
                ),
            )
            event_id = cursor.lastrowid

            new_posture = self._next_posture(str(asset["posture"]), decision.action)
            trust_score = max(0, min(100, int(asset["trust_score"]) - self._trust_penalty(decision.action)))
            db.execute(
                """
                UPDATE assets
                SET trust_score = ?, posture = ?, last_ip = ?, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (trust_score, new_posture, normalize_ip(source_ip), asset_id),
            )

            if decision.action in {"challenge", "block", "quarantine"}:
                db.execute(
                    """
                    INSERT INTO incidents (asset_id, event_id, severity, title, summary, action)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        asset_id,
                        event_id,
                        decision.severity,
                        f"{decision.action.title()} outbound connection",
                        "; ".join(decision.reasons),
                        decision.action,
                    ),
                )

            return self._event_with_related(db, event_id)

    def quarantine_asset(self, asset_id: int, note: str = "Manual quarantine from dashboard") -> dict[str, Any]:
        with self.connect() as db:
            asset = self._get_row(db, "SELECT * FROM assets WHERE id = ?", (asset_id,))
            trust_score = max(0, int(asset["trust_score"]) - 12)
            db.execute(
                """
                UPDATE assets
                SET posture = 'quarantined', trust_score = ?, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (trust_score, asset_id),
            )
            return self._row_to_dict(self._get_row(db, "SELECT * FROM assets WHERE id = ?", (asset_id,)))

    def resolve_incident(self, incident_id: int, note: str = "Resolved by analyst") -> dict[str, Any]:
        with self.connect() as db:
            incident = self._get_row(db, "SELECT * FROM incidents WHERE id = ?", (incident_id,))
            db.execute(
                """
                UPDATE incidents
                SET status = 'resolved', resolution_note = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (note, incident_id),
            )
            remaining = db.execute(
                "SELECT COUNT(*) FROM incidents WHERE asset_id = ? AND status = 'open'",
                (incident["asset_id"],),
            ).fetchone()[0]
            asset = self._get_row(db, "SELECT * FROM assets WHERE id = ?", (incident["asset_id"],))
            if remaining == 0 and asset["posture"] in {"monitored", "challenged"}:
                db.execute("UPDATE assets SET posture = 'healthy' WHERE id = ?", (incident["asset_id"],))
            return self._row_to_dict(self._get_row(db, "SELECT * FROM incidents WHERE id = ?", (incident_id,)))

    def _load_active_policy(self, db: sqlite3.Connection) -> GuardPolicy:
        row = self._get_row(db, "SELECT * FROM policies WHERE enabled = 1 ORDER BY id ASC LIMIT 1", ())
        return GuardPolicy(
            name=str(row["name"]),
            mode=str(row["mode"]),
            trusted_networks=tuple(json.loads(row["trusted_networks_json"] or "[]")),
            block_ports=tuple(int(port) for port in json.loads(row["block_ports_json"] or "[]")),
            hard_block_countries=tuple(json.loads(row["hard_block_countries_json"] or "[]")),
            challenge_threshold=int(row["challenge_threshold"]),
            block_threshold=int(row["block_threshold"]),
            quarantine_threshold=int(row["quarantine_threshold"]),
        )

    def _event_with_related(self, db: sqlite3.Connection, event_id: int) -> dict[str, Any]:
        event = self._row_to_dict(
            self._get_row(
                db,
                """
                SELECT e.*, a.hostname AS asset_name, a.owner AS asset_owner
                FROM events e
                JOIN assets a ON a.id = e.asset_id
                WHERE e.id = ?
                """,
                (event_id,),
            )
        )
        event["reasons"] = json.loads(event.pop("reasons_json") or "[]")
        incident = db.execute("SELECT id FROM incidents WHERE event_id = ?", (event_id,)).fetchone()
        event["incident_id"] = incident[0] if incident else None
        return event

    @staticmethod
    def _next_posture(current: str, action: str) -> str:
        if current == "quarantined":
            return current
        if action == "quarantine":
            return "quarantined"
        if current == "restricted" and action != "quarantine":
            return current
        if action == "block":
            return "restricted"
        if action == "challenge":
            return "challenged"
        if action == "observe" and current == "healthy":
            return "monitored"
        return current

    @staticmethod
    def _trust_penalty(action: str) -> int:
        return {
            "allow": 0,
            "observe": 2,
            "challenge": 7,
            "block": 12,
            "quarantine": 25,
        }.get(action, 0)

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

"""SQLite persistence for Extreme IP Guard."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .anomaly import AnomalyEngine
from .audit_chain import GENESIS_HASH, append_entry
from .core import EnforcementAction, composite_risk_score, evaluate_event, zero_trust_session_verdict


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.anomaly = AnomalyEngine()

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
                CREATE TABLE IF NOT EXISTS endpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT NOT NULL UNIQUE,
                    user_name TEXT NOT NULL DEFAULT '',
                    department TEXT NOT NULL DEFAULT 'General',
                    trust_score INTEGER NOT NULL DEFAULT 70,
                    segment TEXT NOT NULL DEFAULT 'corporate',
                    is_quarantined INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS agents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL UNIQUE,
                    agent_type TEXT NOT NULL,
                    endpoint_id INTEGER REFERENCES endpoints(id),
                    hostname TEXT NOT NULL,
                    os_name TEXT NOT NULL DEFAULT '',
                    version TEXT NOT NULL DEFAULT '',
                    trust_score INTEGER NOT NULL DEFAULT 70,
                    posture_json TEXT NOT NULL DEFAULT '{}',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id INTEGER REFERENCES endpoints(id),
                    agent_id TEXT NOT NULL DEFAULT '',
                    category TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '',
                    severity TEXT NOT NULL DEFAULT 'info',
                    action TEXT NOT NULL DEFAULT 'allow',
                    risk_delta INTEGER NOT NULL DEFAULT 0,
                    anomaly_score INTEGER NOT NULL DEFAULT 0,
                    matched_rule TEXT NOT NULL DEFAULT '',
                    mitre_technique TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    severity TEXT NOT NULL DEFAULT 'medium',
                    endpoint_id INTEGER REFERENCES endpoints(id),
                    event_id INTEGER REFERENCES security_events(id),
                    assignee TEXT NOT NULL DEFAULT 'soc',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    policy_id TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    config_json TEXT NOT NULL DEFAULT '{}'
                );
                """
            )

    def seed_demo(self) -> None:
        with self.connect() as db:
            if db.execute("SELECT COUNT(*) FROM endpoints").fetchone()[0] == 0:
                db.executemany(
                    """
                    INSERT INTO endpoints (hostname, user_name, department, trust_score, segment)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        ("ws-finance-01", "nora.finance", "Finance", 82, "corporate"),
                        ("ws-dev-14", "omar.dev", "Engineering", 68, "corporate"),
                        ("ws-guest-02", "visitor", "Guest", 35, "guest"),
                    ],
                )
            if db.execute("SELECT COUNT(*) FROM policies").fetchone()[0] == 0:
                db.executemany(
                    """
                    INSERT INTO policies (policy_id, name, category, config_json)
                    VALUES (?, ?, ?, ?)
                    """,
                    [
                        ("zt-default", "Zero Trust default gate", "identity", '{"require_mfa": true}'),
                        ("dlp-pci", "PCI-style data patterns", "dlp", '{"block_on_match": true}'),
                        ("net-segment", "Guest isolation", "network", '{"block_lateral_from": ["guest"]}'),
                        ("usb-default", "Removable media control", "usb", '{"default": "warn"}'),
                    ],
                )

    def _audit(self, db: sqlite3.Connection, event_type: str, payload: dict[str, Any]) -> None:
        row = db.execute(
            "SELECT sequence, entry_hash FROM audit_log ORDER BY sequence DESC LIMIT 1"
        ).fetchone()
        sequence = 1 if row is None else int(row["sequence"]) + 1
        previous_hash = GENESIS_HASH if row is None else str(row["entry_hash"])
        created_at = utc_now()
        entry = append_entry(
            sequence=sequence,
            event_type=event_type,
            payload=payload,
            previous_hash=previous_hash,
            created_at=created_at,
        )
        db.execute(
            """
            INSERT INTO audit_log (sequence, event_type, payload_json, previous_hash, entry_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                entry.sequence,
                entry.event_type,
                json.dumps(entry.payload),
                entry.previous_hash,
                entry.entry_hash,
                entry.created_at,
            ),
        )

    def list_endpoints(self) -> list[dict[str, Any]]:
        endpoints = self._fetch_all("SELECT * FROM endpoints ORDER BY hostname")
        for endpoint in endpoints:
            endpoint["risk"] = self._endpoint_risk(endpoint["id"])
        return endpoints

    def list_agents(self) -> list[dict[str, Any]]:
        agents = self._fetch_all("SELECT * FROM agents ORDER BY last_seen DESC")
        for agent in agents:
            agent["posture"] = json.loads(agent.pop("posture_json") or "{}")
            agent["metadata"] = json.loads(agent.pop("metadata_json") or "{}")
        return agents

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT e.*, ep.hostname
            FROM security_events e
            LEFT JOIN endpoints ep ON ep.id = e.endpoint_id
            ORDER BY e.id DESC
            LIMIT ?
            """,
            (limit,),
        )

    def list_incidents(self) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT i.*, ep.hostname
            FROM incidents i
            LEFT JOIN endpoints ep ON ep.id = i.endpoint_id
            ORDER BY i.id DESC
            """
        )

    def list_policies(self) -> list[dict[str, Any]]:
        policies = self._fetch_all("SELECT * FROM policies ORDER BY policy_id")
        for policy in policies:
            policy["config"] = json.loads(policy.pop("config_json") or "{}")
        return policies

    def audit_status(self) -> dict[str, Any]:
        rows = self._fetch_all("SELECT * FROM audit_log ORDER BY sequence")
        from .audit_chain import AuditEntry, verify_chain

        entries = [
            AuditEntry(
                sequence=row["sequence"],
                event_type=row["event_type"],
                payload=json.loads(row["payload_json"]),
                previous_hash=row["previous_hash"],
                entry_hash=row["entry_hash"],
                created_at=row["created_at"],
            )
            for row in rows
        ]
        result = verify_chain(entries)
        result["entries"] = len(entries)
        if entries:
            result["head_hash"] = entries[-1].entry_hash[:16] + "…"
        return result

    def dashboard(self) -> dict[str, Any]:
        with self.connect() as db:
            endpoints = db.execute("SELECT COUNT(*) FROM endpoints").fetchone()[0]
            agents = db.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            events_24h = db.execute(
                """
                SELECT COUNT(*) FROM security_events
                WHERE datetime(created_at) >= datetime('now', '-1 day')
                """
            ).fetchone()[0]
            open_incidents = db.execute(
                "SELECT COUNT(*) FROM incidents WHERE status = 'open'"
            ).fetchone()[0]
            blocked = db.execute(
                "SELECT COUNT(*) FROM security_events WHERE action IN ('block', 'quarantine', 'isolate')"
            ).fetchone()[0]
            quarantined = db.execute(
                "SELECT COUNT(*) FROM endpoints WHERE is_quarantined = 1"
            ).fetchone()[0]
        return {
            "endpoints": endpoints,
            "agents": agents,
            "events_24h": events_24h,
            "open_incidents": open_incidents,
            "blocked_events": blocked,
            "quarantined_endpoints": quarantined,
            "platform": "Extreme IP Guard",
            "version": "0.1.0",
        }

    def register_agent(self, payload: dict[str, Any]) -> dict[str, Any]:
        agent_id = str(payload["agent_id"])
        now = utc_now()
        posture = payload.get("posture") or {}
        trust = int(payload.get("trust_score", 70))
        with self.connect() as db:
            endpoint_id = self._ensure_endpoint(
                db,
                hostname=str(payload.get("hostname", agent_id)),
                user_name=str(payload.get("user_name", "")),
                trust_score=trust,
            )
            existing = db.execute(
                "SELECT id FROM agents WHERE agent_id = ?", (agent_id,)
            ).fetchone()
            if existing:
                db.execute(
                    """
                    UPDATE agents
                    SET last_seen = ?, trust_score = ?, posture_json = ?, version = ?, endpoint_id = ?
                    WHERE agent_id = ?
                    """,
                    (
                        now,
                        trust,
                        json.dumps(posture),
                        str(payload.get("version", "")),
                        endpoint_id,
                        agent_id,
                    ),
                )
            else:
                db.execute(
                    """
                    INSERT INTO agents
                        (agent_id, agent_type, endpoint_id, hostname, os_name, version,
                         trust_score, posture_json, metadata_json, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        agent_id,
                        str(payload.get("agent_type", "endpoint")),
                        endpoint_id,
                        str(payload.get("hostname", "")),
                        str(payload.get("os_name", "")),
                        str(payload.get("version", "")),
                        trust,
                        json.dumps(posture),
                        json.dumps(payload.get("metadata") or {}),
                        now,
                    ),
                )
            self._audit(db, "agent.heartbeat", {"agent_id": agent_id, "trust_score": trust})
        return {"status": "ok", "agent_id": agent_id, "server_time": now}

    def ingest_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        category = str(payload.get("category", "endpoint"))
        summary = str(payload.get("summary", ""))
        detail = str(payload.get("detail", ""))
        hostname = str(payload.get("hostname", "unknown"))
        agent_id = str(payload.get("agent_id", ""))
        now = utc_now()

        with self.connect() as db:
            endpoint = db.execute(
                "SELECT * FROM endpoints WHERE hostname = ?", (hostname,)
            ).fetchone()
            if endpoint is None:
                endpoint_id = self._ensure_endpoint(db, hostname=hostname)
                endpoint = db.execute(
                    "SELECT * FROM endpoints WHERE id = ?", (endpoint_id,)
                ).fetchone()
            else:
                endpoint_id = int(endpoint["id"])

            entity = str(endpoint["user_name"] or hostname)
            self.anomaly.record(entity, category=category, timestamp=now)
            anomaly = self.anomaly.score(entity, category=category, timestamp=now)

            decision = evaluate_event(
                category=category,
                summary=summary,
                detail=detail,
                endpoint_trust=int(endpoint["trust_score"]),
            )

            recent = [
                int(row[0])
                for row in db.execute(
                    """
                    SELECT risk_delta FROM security_events
                    WHERE endpoint_id = ?
                    ORDER BY id DESC LIMIT 20
                    """,
                    (endpoint_id,),
                ).fetchall()
            ]
            risk = composite_risk_score(
                base_trust=int(endpoint["trust_score"]),
                recent_event_deltas=recent,
                anomaly_score=int(anomaly["score"]),
            )

            db.execute(
                """
                INSERT INTO security_events
                    (endpoint_id, agent_id, category, summary, detail, severity, action,
                     risk_delta, anomaly_score, matched_rule, mitre_technique, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    endpoint_id,
                    agent_id,
                    category,
                    summary,
                    detail,
                    decision.severity.value,
                    decision.action.value,
                    decision.risk_delta,
                    int(anomaly["score"]),
                    decision.matched_rule_id,
                    decision.mitre_technique,
                    now,
                ),
            )
            event_id = int(db.execute("SELECT last_insert_rowid()").fetchone()[0])

            if decision.action in (
                EnforcementAction.QUARANTINE,
                EnforcementAction.ISOLATE,
            ):
                db.execute(
                    "UPDATE endpoints SET is_quarantined = 1 WHERE id = ?", (endpoint_id,)
                )

            if decision.action != EnforcementAction.ALLOW or int(anomaly["score"]) >= 40:
                db.execute(
                    """
                    INSERT INTO incidents (title, status, severity, endpoint_id, event_id, notes)
                    VALUES (?, 'open', ?, ?, ?, ?)
                    """,
                    (
                        f"{decision.action.value}: {summary[:80]}",
                        decision.severity.value,
                        endpoint_id,
                        event_id,
                        decision.reason,
                    ),
                )

            self._audit(
                db,
                "security.event",
                {
                    "event_id": event_id,
                    "category": category,
                    "action": decision.action.value,
                    "risk_level": risk.level,
                },
            )

        return {
            "event_id": event_id,
            "decision": {
                "action": decision.action.value,
                "severity": decision.severity.value,
                "reason": decision.reason,
                "matched_rule": decision.matched_rule_id,
                "mitre": decision.mitre_technique,
            },
            "risk": {"score": risk.score, "level": risk.level, "factors": list(risk.factors)},
            "anomaly": anomaly,
        }

    def zero_trust_check(self, payload: dict[str, Any]) -> dict[str, Any]:
        verdict = zero_trust_session_verdict(
            device_posture=dict(payload.get("posture") or {}),
            user_mfa=bool(payload.get("user_mfa")),
            network_segment=str(payload.get("segment", "corporate")),
        )
        with self.connect() as db:
            self._audit(db, "zt.session_check", verdict)
        return verdict

    def resolve_incident(self, incident_id: int, note: str = "") -> dict[str, Any]:
        now = utc_now()
        with self.connect() as db:
            db.execute(
                """
                UPDATE incidents
                SET status = 'resolved', resolved_at = ?, notes = CASE
                    WHEN notes = '' THEN ? ELSE notes || ' | ' || ?
                END
                WHERE id = ?
                """,
                (now, note, note, incident_id),
            )
            self._audit(db, "incident.resolve", {"incident_id": incident_id, "note": note})
        row = self._fetch_one("SELECT * FROM incidents WHERE id = ?", (incident_id,))
        if row is None:
            raise ValueError("incident not found")
        return row

    def release_quarantine(self, endpoint_id: int) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                "UPDATE endpoints SET is_quarantined = 0 WHERE id = ?", (endpoint_id,)
            )
            self._audit(db, "endpoint.release_quarantine", {"endpoint_id": endpoint_id})
        row = self._fetch_one("SELECT * FROM endpoints WHERE id = ?", (endpoint_id,))
        if row is None:
            raise ValueError("endpoint not found")
        row["risk"] = self._endpoint_risk(endpoint_id)
        return row

    def _endpoint_risk(self, endpoint_id: int) -> dict[str, Any]:
        with self.connect() as db:
            endpoint = db.execute(
                "SELECT trust_score FROM endpoints WHERE id = ?", (endpoint_id,)
            ).fetchone()
            if endpoint is None:
                return {"score": 0, "level": "unknown", "factors": []}
            recent = [
                int(row[0])
                for row in db.execute(
                    """
                    SELECT risk_delta FROM security_events
                    WHERE endpoint_id = ?
                    ORDER BY id DESC LIMIT 20
                    """,
                    (endpoint_id,),
                ).fetchall()
            ]
        profile = composite_risk_score(
            base_trust=int(endpoint["trust_score"]),
            recent_event_deltas=recent,
        )
        return {"score": profile.score, "level": profile.level, "factors": list(profile.factors)}

    def _ensure_endpoint(
        self,
        db: sqlite3.Connection,
        *,
        hostname: str,
        user_name: str = "",
        trust_score: int = 70,
    ) -> int:
        row = db.execute(
            "SELECT id FROM endpoints WHERE hostname = ?", (hostname,)
        ).fetchone()
        if row:
            return int(row["id"])
        db.execute(
            """
            INSERT INTO endpoints (hostname, user_name, trust_score)
            VALUES (?, ?, ?)
            """,
            (hostname, user_name, trust_score),
        )
        return int(db.execute("SELECT last_insert_rowid()").fetchone()[0])

    def _fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def _fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(query, params).fetchone()
        return dict(row) if row else None

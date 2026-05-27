"""SQLite persistence for the Xtreme IP Guard prototype."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .core import EndpointEvent, PolicyRule, evaluate_event


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_schema(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS endpoints (
                    endpoint_id TEXT PRIMARY KEY,
                    hostname TEXT NOT NULL,
                    os_name TEXT NOT NULL DEFAULT '',
                    owner TEXT NOT NULL DEFAULT '',
                    trust_score INTEGER NOT NULL DEFAULT 70,
                    isolated INTEGER NOT NULL DEFAULT 0,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    agent_type TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    os_name TEXT NOT NULL DEFAULT '',
                    version TEXT NOT NULL DEFAULT '',
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS policies (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    event_type TEXT NOT NULL DEFAULT '*',
                    classification TEXT NOT NULL DEFAULT '*',
                    channel TEXT NOT NULL DEFAULT '*',
                    destination_contains TEXT NOT NULL DEFAULT '',
                    min_risk INTEGER NOT NULL DEFAULT 0,
                    reason TEXT NOT NULL DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    destination TEXT NOT NULL DEFAULT '',
                    process TEXT NOT NULL DEFAULT '',
                    severity INTEGER NOT NULL,
                    behavior_flags TEXT NOT NULL DEFAULT '[]',
                    risk_score INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    matched_rule_id TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target TEXT NOT NULL DEFAULT '',
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def seed_demo(self) -> None:
        demo_policies = [
            PolicyRule(
                rule_id="XIG-DLP-USB-SECRET",
                name="Block secret data copied to removable media",
                action="block",
                event_type="file_copy",
                classification="secret",
                channel="removable_media",
                reason="Secret data cannot leave managed storage through USB media",
            ),
            PolicyRule(
                rule_id="XIG-DLP-PERSONAL-MAIL",
                name="Quarantine confidential data sent to personal email",
                action="quarantine",
                classification="confidential",
                channel="personal_email",
                reason="Confidential data sent to personal email requires investigation",
            ),
            PolicyRule(
                rule_id="XIG-SOURCE-UNSANCTIONED-CLOUD",
                name="Block source code upload to unsanctioned cloud",
                action="block",
                classification="source_code",
                channel="unsanctioned_cloud",
                reason="Source code is restricted to approved repositories and storage",
            ),
            PolicyRule(
                rule_id="XIG-CREDENTIAL-HIGH-RISK",
                name="Isolate endpoints involved in credential exfiltration",
                action="isolate_endpoint",
                classification="credential",
                min_risk=80,
                reason="Credential movement at high risk requires automatic containment",
            ),
        ]

        with self.connect() as db:
            for policy in demo_policies:
                db.execute(
                    """
                    INSERT OR IGNORE INTO policies (
                        rule_id, name, action, event_type, classification, channel,
                        destination_contains, min_risk, reason, enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        policy.rule_id,
                        policy.name,
                        policy.action,
                        policy.event_type,
                        policy.classification,
                        policy.channel,
                        policy.destination_contains,
                        policy.min_risk,
                        policy.reason,
                        int(policy.enabled),
                    ),
                )

            db.execute(
                """
                INSERT OR IGNORE INTO endpoints (
                    endpoint_id, hostname, os_name, owner, trust_score, metadata
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "endpoint-demo-001",
                    "FUTURE-LAPTOP-001",
                    "Windows 11 Enterprise",
                    "sara",
                    76,
                    json.dumps({"site": "HQ", "department": "Finance"}),
                ),
            )

    def dashboard(self) -> dict[str, Any]:
        with self.connect() as db:
            totals = {
                "endpoints": db.execute("SELECT COUNT(*) FROM endpoints").fetchone()[0],
                "isolated_endpoints": db.execute("SELECT COUNT(*) FROM endpoints WHERE isolated = 1").fetchone()[0],
                "policies": db.execute("SELECT COUNT(*) FROM policies WHERE enabled = 1").fetchone()[0],
                "events": db.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                "blocked_or_quarantined": db.execute(
                    "SELECT COUNT(*) FROM events WHERE action IN ('block', 'quarantine', 'isolate_endpoint')"
                ).fetchone()[0],
            }
            recent_events = [dict(row) for row in db.execute("SELECT * FROM events ORDER BY event_id DESC LIMIT 10")]
            top_actions = [
                dict(row)
                for row in db.execute(
                    "SELECT action, COUNT(*) AS count FROM events GROUP BY action ORDER BY count DESC, action"
                )
            ]
            return {"totals": totals, "recent_events": recent_events, "top_actions": top_actions}

    def list_endpoints(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [self._decode_endpoint(row) for row in db.execute("SELECT * FROM endpoints ORDER BY hostname")]

    def list_policies(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [self._decode_policy(row) for row in db.execute("SELECT * FROM policies ORDER BY rule_id")]

    def list_events(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [self._decode_event(row) for row in db.execute("SELECT * FROM events ORDER BY event_id DESC LIMIT 100")]

    def list_agents(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [self._decode_agent(row) for row in db.execute("SELECT * FROM agents ORDER BY hostname")]

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
        metadata = metadata or {}
        endpoint_id = str(metadata.get("endpoint_id") or agent_id)
        owner = str(metadata.get("owner") or "")

        with self.connect() as db:
            db.execute(
                """
                INSERT INTO agents (agent_id, agent_type, hostname, os_name, version, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    agent_type = excluded.agent_type,
                    hostname = excluded.hostname,
                    os_name = excluded.os_name,
                    version = excluded.version,
                    metadata = excluded.metadata,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (agent_id, agent_type, hostname, os_name, version, json.dumps(metadata, sort_keys=True)),
            )
            db.execute(
                """
                INSERT INTO endpoints (endpoint_id, hostname, os_name, owner, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(endpoint_id) DO UPDATE SET
                    hostname = excluded.hostname,
                    os_name = excluded.os_name,
                    owner = COALESCE(NULLIF(excluded.owner, ''), owner),
                    metadata = excluded.metadata,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (endpoint_id, hostname, os_name, owner, json.dumps(metadata, sort_keys=True)),
            )
            row = db.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,)).fetchone()
            return self._decode_agent(row)

    def ingest_event(self, event: EndpointEvent) -> dict[str, Any]:
        policies = [self._policy_from_row(row) for row in self._policy_rows()]
        endpoint = self.get_or_create_endpoint(event.endpoint_id, owner=event.actor)
        decision = evaluate_event(event, policies, endpoint_trust=int(endpoint["trust_score"]))

        with self.connect() as db:
            db.execute(
                """
                INSERT INTO events (
                    endpoint_id, actor, event_type, channel, resource, classification,
                    destination, process, severity, behavior_flags, risk_score, action,
                    reason, matched_rule_id, tags, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.endpoint_id,
                    event.actor,
                    event.event_type,
                    event.channel,
                    event.resource,
                    event.classification,
                    event.destination,
                    event.process,
                    event.severity,
                    json.dumps(list(event.behavior_flags), sort_keys=True),
                    decision.risk_score,
                    decision.action,
                    decision.reason,
                    decision.matched_rule_id,
                    json.dumps(list(decision.tags), sort_keys=True),
                    json.dumps(event.metadata, sort_keys=True),
                ),
            )
            if decision.action == "isolate_endpoint":
                db.execute("UPDATE endpoints SET isolated = 1 WHERE endpoint_id = ?", (event.endpoint_id,))
            row = db.execute("SELECT * FROM events ORDER BY event_id DESC LIMIT 1").fetchone()
            return self._decode_event(row)

    def create_policy(self, policy: PolicyRule) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO policies (
                    rule_id, name, action, event_type, classification, channel,
                    destination_contains, min_risk, reason, enabled
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    policy.rule_id,
                    policy.name,
                    policy.action,
                    policy.event_type,
                    policy.classification,
                    policy.channel,
                    policy.destination_contains,
                    policy.min_risk,
                    policy.reason,
                    int(policy.enabled),
                ),
            )
            row = db.execute("SELECT * FROM policies WHERE rule_id = ?", (policy.rule_id,)).fetchone()
            return self._decode_policy(row)

    def set_endpoint_isolation(self, endpoint_id: str, isolated: bool) -> dict[str, Any]:
        self.get_or_create_endpoint(endpoint_id)
        with self.connect() as db:
            db.execute("UPDATE endpoints SET isolated = ? WHERE endpoint_id = ?", (int(isolated), endpoint_id))
            row = db.execute("SELECT * FROM endpoints WHERE endpoint_id = ?", (endpoint_id,)).fetchone()
            return self._decode_endpoint(row)

    def record_audit(
        self,
        actor: str,
        action: str,
        *,
        target: str = "",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = json.dumps(details or {}, sort_keys=True)
        with self.connect() as db:
            db.execute(
                "INSERT INTO audit_log (actor, action, target, details) VALUES (?, ?, ?, ?)",
                (actor, action, target, payload),
            )
            row = db.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
            return self._decode_audit(row)

    def list_audit(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT ?",
                (limit,),
            )
            return [self._decode_audit(row) for row in rows]

    def endpoint_directives(self, endpoint_id: str) -> dict[str, Any]:
        endpoint = self.get_or_create_endpoint(endpoint_id)
        policies = self.list_policies()
        active = [policy for policy in policies if policy.get("enabled")]
        return {
            "endpoint_id": endpoint_id,
            "isolated": bool(endpoint.get("isolated")),
            "trust_score": int(endpoint.get("trust_score", 70)),
            "policy_count": len(active),
            "policies": active,
            "actions": ["allow", "monitor", "warn", "block", "quarantine", "isolate_endpoint"],
        }

    def get_or_create_endpoint(self, endpoint_id: str, *, owner: str = "") -> dict[str, Any]:
        with self.connect() as db:
            row = db.execute("SELECT * FROM endpoints WHERE endpoint_id = ?", (endpoint_id,)).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO endpoints (endpoint_id, hostname, owner) VALUES (?, ?, ?)",
                    (endpoint_id, endpoint_id, owner),
                )
                row = db.execute("SELECT * FROM endpoints WHERE endpoint_id = ?", (endpoint_id,)).fetchone()
            return self._decode_endpoint(row)

    def _policy_rows(self) -> list[sqlite3.Row]:
        with self.connect() as db:
            return list(db.execute("SELECT * FROM policies WHERE enabled = 1 ORDER BY rule_id"))

    @staticmethod
    def _policy_from_row(row: sqlite3.Row) -> PolicyRule:
        return PolicyRule(
            rule_id=row["rule_id"],
            name=row["name"],
            action=row["action"],
            event_type=row["event_type"],
            classification=row["classification"],
            channel=row["channel"],
            destination_contains=row["destination_contains"],
            min_risk=row["min_risk"],
            reason=row["reason"],
            enabled=bool(row["enabled"]),
        )

    @staticmethod
    def _decode_json(value: str, fallback: Any) -> Any:
        try:
            return json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return fallback

    def _decode_endpoint(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["isolated"] = bool(data["isolated"])
        data["metadata"] = self._decode_json(data["metadata"], {})
        return data

    def _decode_policy(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["enabled"] = bool(data["enabled"])
        return data

    def _decode_event(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["behavior_flags"] = self._decode_json(data["behavior_flags"], [])
        data["tags"] = self._decode_json(data["tags"], [])
        data["metadata"] = self._decode_json(data["metadata"], {})
        return data

    def _decode_agent(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metadata"] = self._decode_json(data["metadata"], {})
        return data

    def _decode_audit(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["details"] = self._decode_json(data["details"], {})
        return data

"""SQLite persistence for the Xtreme IP Guard prototype."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .ai.baseline import OnlineStats
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

                CREATE TABLE IF NOT EXISTS ai_baselines (
                    baseline_key TEXT PRIMARY KEY,
                    endpoint_id TEXT NOT NULL,
                    signal_name TEXT NOT NULL DEFAULT 'risk',
                    sample_count INTEGER NOT NULL DEFAULT 0,
                    mean_value REAL NOT NULL DEFAULT 0,
                    m2_value REAL NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS ai_insights (
                    insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id TEXT NOT NULL,
                    event_id INTEGER,
                    insight_type TEXT NOT NULL,
                    severity REAL NOT NULL,
                    summary TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS ai_predictions (
                    prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id TEXT NOT NULL,
                    predicted_risk REAL NOT NULL,
                    breach_probability REAL NOT NULL,
                    horizon_hours INTEGER NOT NULL DEFAULT 24,
                    payload TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS threat_intel_cache (
                    indicator TEXT PRIMARY KEY,
                    ioc_type TEXT NOT NULL DEFAULT 'domain',
                    severity INTEGER NOT NULL DEFAULT 50,
                    source TEXT NOT NULL DEFAULT 'mersal-feed',
                    metadata TEXT NOT NULL DEFAULT '{}',
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
        from .ai import MersalAICortex

        policies = [self._policy_from_row(row) for row in self._policy_rows()]
        endpoint = self.get_or_create_endpoint(event.endpoint_id, owner=event.actor)
        decision = evaluate_event(event, policies, endpoint_trust=int(endpoint["trust_score"]))
        fusion = MersalAICortex(self).analyze_and_fuse(
            event,
            decision,
            endpoint_trust=int(endpoint["trust_score"]),
        )

        tags = list(decision.tags)
        if fusion.ai_escalated and "ai-escalated" not in tags:
            tags.append("ai-escalated")
        metadata = {
            **dict(event.metadata),
            "ai": {
                "anomaly_score": fusion.anomaly_score,
                "predicted_risk": fusion.predicted_risk,
                "breach_probability": fusion.breach_probability,
                "confidence": fusion.confidence,
                "ai_escalated": fusion.ai_escalated,
                "signals": fusion.signals,
                "ioc_hits": [dict(hit) for hit in fusion.ioc_hits],
            },
        }

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
                    fusion.risk_score,
                    fusion.action,
                    fusion.reason,
                    decision.matched_rule_id,
                    json.dumps(tags, sort_keys=True),
                    json.dumps(metadata, sort_keys=True),
                ),
            )
            event_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            if fusion.action == "isolate_endpoint":
                db.execute("UPDATE endpoints SET isolated = 1 WHERE endpoint_id = ?", (event.endpoint_id,))
            row = db.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()

        self.record_ai_insight(
            endpoint_id=event.endpoint_id,
            event_id=int(event_id),
            insight_type="anomaly" if fusion.anomaly_score >= 40 else "prediction",
            severity=fusion.anomaly_score,
            summary=fusion.reason,
            payload={
                "action": fusion.action,
                "risk_score": fusion.risk_score,
                "ai_escalated": fusion.ai_escalated,
                "signals": fusion.signals,
            },
        )
        self.record_ai_prediction(
            endpoint_id=event.endpoint_id,
            predicted_risk=fusion.predicted_risk,
            breach_probability=fusion.breach_probability,
            payload=fusion.signals.get("prediction", {}),
        )
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

    def get_baseline(self, baseline_key: str) -> OnlineStats:
        with self.connect() as db:
            row = db.execute(
                "SELECT sample_count, mean_value, m2_value FROM ai_baselines WHERE baseline_key = ?",
                (baseline_key,),
            ).fetchone()
            if row is None:
                return OnlineStats()
            return OnlineStats.from_row(int(row["sample_count"]), float(row["mean_value"]), float(row["m2_value"]))

    def save_baseline(self, baseline_key: str, endpoint_id: str, signal_name: str, stats: OnlineStats) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO ai_baselines (
                    baseline_key, endpoint_id, signal_name, sample_count, mean_value, m2_value
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(baseline_key) DO UPDATE SET
                    endpoint_id = excluded.endpoint_id,
                    signal_name = excluded.signal_name,
                    sample_count = excluded.sample_count,
                    mean_value = excluded.mean_value,
                    m2_value = excluded.m2_value,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (baseline_key, endpoint_id, signal_name, stats.count, stats.mean, stats.m2),
            )

    def count_baselines(self) -> int:
        with self.connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM ai_baselines").fetchone()[0])

    def recent_risks_for_endpoint(self, endpoint_id: str, *, limit: int = 12) -> list[float]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT risk_score FROM events WHERE endpoint_id = ? ORDER BY event_id DESC LIMIT ?",
                (endpoint_id, limit),
            )
            return [float(row["risk_score"]) for row in rows]

    def record_ai_insight(
        self,
        *,
        endpoint_id: str,
        event_id: int | None,
        insight_type: str,
        severity: float,
        summary: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO ai_insights (
                    endpoint_id, event_id, insight_type, severity, summary, payload
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    endpoint_id,
                    event_id,
                    insight_type,
                    severity,
                    summary,
                    json.dumps(payload or {}, sort_keys=True),
                ),
            )

    def list_ai_insights(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM ai_insights ORDER BY insight_id DESC LIMIT ?",
                (limit,),
            )
            return [self._decode_ai_insight(row) for row in rows]

    def record_ai_prediction(
        self,
        *,
        endpoint_id: str,
        predicted_risk: float,
        breach_probability: float,
        horizon_hours: int = 24,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO ai_predictions (
                    endpoint_id, predicted_risk, breach_probability, horizon_hours, payload
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    endpoint_id,
                    predicted_risk,
                    breach_probability,
                    horizon_hours,
                    json.dumps(payload or {}, sort_keys=True),
                ),
            )

    def list_ai_predictions(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM ai_predictions ORDER BY prediction_id DESC LIMIT ?",
                (limit,),
            )
            return [self._decode_ai_prediction(row) for row in rows]

    def list_threat_intel(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM threat_intel_cache ORDER BY severity DESC, indicator")
            return [self._decode_threat_intel(row) for row in rows]

    def seed_threat_intel(self, indicators: list[dict[str, Any]]) -> int:
        inserted = 0
        with self.connect() as db:
            for item in indicators:
                cursor = db.execute(
                    """
                    INSERT OR IGNORE INTO threat_intel_cache (
                        indicator, ioc_type, severity, source, metadata
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(item.get("indicator", "")),
                        str(item.get("ioc_type", "domain")),
                        int(item.get("severity", 50)),
                        str(item.get("source", "mersal-feed")),
                        json.dumps({k: v for k, v in item.items() if k not in {"indicator", "ioc_type", "severity", "source"}}, sort_keys=True),
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def high_risk_patterns(self, *, limit: int = 5) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT channel, classification, COUNT(*) AS hits
                FROM events
                WHERE risk_score >= 70
                GROUP BY channel, classification
                ORDER BY hits DESC, channel, classification
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in rows]

    def train_cortex_from_history(self, *, limit: int = 100) -> dict[str, Any]:
        with self.connect() as db:
            rows = list(
                db.execute(
                    """
                    SELECT endpoint_id, channel, classification, risk_score
                    FROM events
                    ORDER BY event_id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            )
        trained = 0
        for row in rows:
            baseline_key = f"{row['endpoint_id']}:{row['channel']}:{row['classification']}"
            stats = self.get_baseline(baseline_key)
            stats.update(float(row["risk_score"]))
            self.save_baseline(baseline_key, row["endpoint_id"], "risk", stats)
            trained += 1
        if not self.list_threat_intel():
            from .ai.threat_intel import DEFAULT_IOCS

            self.seed_threat_intel(DEFAULT_IOCS)
        return {"trained_samples": trained, "baseline_signals": self.count_baselines()}

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

    def _decode_ai_insight(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = self._decode_json(data["payload"], {})
        return data

    def _decode_ai_prediction(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = self._decode_json(data["payload"], {})
        return data

    def _decode_threat_intel(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metadata"] = self._decode_json(data["metadata"], {})
        return data

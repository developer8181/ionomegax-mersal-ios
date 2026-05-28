# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
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

                CREATE TABLE IF NOT EXISTS vuln_scans (
                    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scope TEXT NOT NULL DEFAULT 'daily',
                    status TEXT NOT NULL DEFAULT 'running',
                    findings_count INTEGER NOT NULL DEFAULT 0,
                    summary TEXT NOT NULL DEFAULT '{}',
                    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS vuln_findings (
                    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER,
                    endpoint_id TEXT NOT NULL,
                    cve_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    severity REAL NOT NULL,
                    port INTEGER NOT NULL DEFAULT 0,
                    service TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'open',
                    remediation TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS threat_feed_sync (
                    sync_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_name TEXT NOT NULL,
                    indicators_added INTEGER NOT NULL DEFAULT 0,
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS soar_playbooks (
                    playbook_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    config TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS soar_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playbook_id TEXT NOT NULL,
                    endpoint_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    actions TEXT NOT NULL DEFAULT '[]',
                    trigger_ref TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS security_posture (
                    posture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    score INTEGER NOT NULL,
                    grade TEXT NOT NULL,
                    breakdown TEXT NOT NULL DEFAULT '{}',
                    computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS scheduler_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS siem_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    condition_json TEXT NOT NULL DEFAULT '{}',
                    severity INTEGER NOT NULL DEFAULT 50,
                    enabled INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS siem_alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    endpoint_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'open',
                    event_ids TEXT NOT NULL DEFAULT '[]',
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    status TEXT NOT NULL DEFAULT 'open',
                    assignee TEXT NOT NULL DEFAULT 'soc-team',
                    endpoint_id TEXT NOT NULL DEFAULT '',
                    summary TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS incident_timeline (
                    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    incident_id TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS compliance_controls (
                    control_id TEXT PRIMARY KEY,
                    framework TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT '',
                    weight INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS compliance_scores (
                    score_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    framework TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    passed INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    breakdown TEXT NOT NULL DEFAULT '{}',
                    computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS edr_detections (
                    detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id TEXT NOT NULL,
                    detection_type TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    details TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS network_flows (
                    flow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_id TEXT NOT NULL,
                    protocol TEXT NOT NULL DEFAULT 'tcp',
                    local_addr TEXT NOT NULL,
                    remote_addr TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT '',
                    risk INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS log_records (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    host TEXT NOT NULL DEFAULT '',
                    facility TEXT NOT NULL DEFAULT '',
                    severity INTEGER NOT NULL DEFAULT 30,
                    message TEXT NOT NULL,
                    raw TEXT NOT NULL DEFAULT '',
                    endpoint_id TEXT NOT NULL DEFAULT '',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS suricata_alerts (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signature_id INTEGER NOT NULL,
                    signature TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT '',
                    severity INTEGER NOT NULL DEFAULT 50,
                    src_ip TEXT NOT NULL DEFAULT '',
                    dest_ip TEXT NOT NULL DEFAULT '',
                    proto TEXT NOT NULL DEFAULT '',
                    mitre_technique TEXT NOT NULL DEFAULT '',
                    payload TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS xdr_findings (
                    finding_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    severity INTEGER NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.8,
                    status TEXT NOT NULL DEFAULT 'open',
                    endpoint_id TEXT NOT NULL DEFAULT '',
                    sources TEXT NOT NULL DEFAULT '[]',
                    mitre_techniques TEXT NOT NULL DEFAULT '[]',
                    recommended_action TEXT NOT NULL DEFAULT 'investigate',
                    details TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS yara_rules (
                    rule_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    pattern TEXT NOT NULL,
                    target TEXT NOT NULL DEFAULT 'process',
                    severity INTEGER NOT NULL DEFAULT 70,
                    mitre_technique TEXT NOT NULL DEFAULT '',
                    enabled INTEGER NOT NULL DEFAULT 1
                );
                """
            )
        from .migrations_v6 import apply_v6_migrations
        from .migrations_v7 import apply_v7_migrations

        with self.connect() as db:
            apply_v6_migrations(db)
            apply_v7_migrations(db)

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
                "open_vulns": db.execute(
                    "SELECT COUNT(*) FROM vuln_findings WHERE status = 'open'"
                ).fetchone()[0],
                "critical_vulns": db.execute(
                    "SELECT COUNT(*) FROM vuln_findings WHERE status = 'open' AND severity >= 9"
                ).fetchone()[0],
            }
            posture_row = db.execute(
                "SELECT score, grade FROM security_posture ORDER BY posture_id DESC LIMIT 1"
            ).fetchone()
            posture = dict(posture_row) if posture_row else {"score": 0, "grade": "-"}
            recent_events = [dict(row) for row in db.execute("SELECT * FROM events ORDER BY event_id DESC LIMIT 10")]
            top_actions = [
                dict(row)
                for row in db.execute(
                    "SELECT action, COUNT(*) AS count FROM events GROUP BY action ORDER BY count DESC, action"
                )
            ]
            return {
                "totals": totals,
                "posture": posture,
                "recent_events": recent_events,
                "top_actions": top_actions,
            }

    def list_endpoints(self, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as db:
            if tenant_id:
                rows = db.execute(
                    "SELECT * FROM endpoints WHERE tenant_id = ? ORDER BY hostname",
                    (tenant_id,),
                )
            else:
                rows = db.execute("SELECT * FROM endpoints ORDER BY hostname")
            return [self._decode_endpoint(row) for row in rows]

    def list_policies(self, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as db:
            if tenant_id:
                rows = db.execute(
                    "SELECT * FROM policies WHERE tenant_id = ? ORDER BY rule_id",
                    (tenant_id,),
                )
            else:
                rows = db.execute("SELECT * FROM policies ORDER BY rule_id")
            return [self._decode_policy(row) for row in rows]

    def list_events(self, *, tenant_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as db:
            if tenant_id:
                rows = db.execute(
                    "SELECT * FROM events WHERE tenant_id = ? ORDER BY event_id DESC LIMIT ?",
                    (tenant_id, limit),
                )
            else:
                rows = db.execute(
                    "SELECT * FROM events ORDER BY event_id DESC LIMIT ?",
                    (limit,),
                )
            return [self._decode_event(row) for row in rows]

    def list_agents(self, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as db:
            if tenant_id:
                rows = db.execute(
                    "SELECT * FROM agents WHERE tenant_id = ? ORDER BY hostname",
                    (tenant_id,),
                )
            else:
                rows = db.execute("SELECT * FROM agents ORDER BY hostname")
            return [self._decode_agent(row) for row in rows]

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
        decoded = self._decode_event(row)
        from .soar import SoarEngine

        SoarEngine(self).on_event_ingested(decoded)
        try:
            from .siem.correlator import SiemCorrelator
            from .incidents.manager import IncidentManager

            alerts = SiemCorrelator(self).process_event(decoded)
            from .siem.window_correlator import WindowCorrelator

            alerts.extend(WindowCorrelator(self).process_event(decoded))
            if alerts:
                IncidentManager(self).sync_from_alerts(alerts)
            if int(decoded.get("risk_score", 0)) >= 50:
                self.ingest_log_record(
                    source="dlp-event",
                    message=f"{decoded.get('event_type')}: {decoded.get('resource')} -> {decoded.get('action')}",
                    host=str(decoded.get("endpoint_id", "")),
                    severity=int(decoded.get("risk_score", 30)),
                    endpoint_id=str(decoded.get("endpoint_id", "")),
                    metadata={"event_id": decoded.get("event_id"), "channel": decoded.get("channel")},
                )
        except Exception:  # noqa: BLE001 — enterprise modules must not break ingest
            pass
        return decoded

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
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        from .audit.chain import AuditChain

        payload = details or {}
        with self.connect() as db:
            chain = AuditChain(db)
            prev_hash, record_hash = chain.seal_record(
                actor=actor,
                action=action,
                target=target,
                details=payload,
                tenant_id=tenant_id,
            )
            db.execute(
                """
                INSERT INTO audit_log (actor, action, target, details, tenant_id, prev_hash, record_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    actor,
                    action,
                    target,
                    json.dumps(payload, sort_keys=True),
                    tenant_id,
                    prev_hash,
                    record_hash,
                ),
            )
            row = db.execute("SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT 1").fetchone()
            return self._decode_audit(row)

    def list_audit(self, *, limit: int = 50, tenant_id: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as db:
            if tenant_id:
                rows = db.execute(
                    "SELECT * FROM audit_log WHERE tenant_id = ? ORDER BY audit_id DESC LIMIT ?",
                    (tenant_id, limit),
                )
            else:
                rows = db.execute(
                    "SELECT * FROM audit_log ORDER BY audit_id DESC LIMIT ?",
                    (limit,),
                )
            return [self._decode_audit(row) for row in rows]

    def verify_audit_chain(self, *, limit: int = 500) -> dict[str, Any]:
        with self.connect() as db:
            from .audit.chain import AuditChain

            return AuditChain(db).verify_chain(limit=limit)

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

    def threat_intel_summary(self) -> dict[str, Any]:
        with self.connect() as db:
            total = db.execute("SELECT COUNT(*) FROM threat_intel_cache").fetchone()[0]
            kev = db.execute(
                "SELECT COUNT(*) FROM threat_intel_cache WHERE source = 'cisa-kev'"
            ).fetchone()[0]
            by_source = [
                dict(row)
                for row in db.execute(
                    """
                    SELECT source, COUNT(*) AS count
                    FROM threat_intel_cache
                    GROUP BY source
                    ORDER BY count DESC
                    """
                )
            ]
            recent = db.execute(
                "SELECT * FROM threat_feed_sync ORDER BY sync_id DESC LIMIT 5"
            ).fetchall()
        return {
            "total_indicators": total,
            "cisa_kev_count": kev,
            "by_source": by_source,
            "recent_syncs": [dict(row) for row in recent],
            "top_indicators": self.list_threat_intel()[:15],
        }

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

    def start_vuln_scan(self, *, scope: str = "daily") -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                "INSERT INTO vuln_scans (scope, status) VALUES (?, 'running')",
                (scope,),
            )
            row = db.execute("SELECT * FROM vuln_scans ORDER BY scan_id DESC LIMIT 1").fetchone()
            return dict(row)

    def finish_vuln_scan(self, scan_id: int, *, findings_count: int) -> dict[str, Any]:
        summary = json.dumps({"findings_count": findings_count}, sort_keys=True)
        with self.connect() as db:
            db.execute(
                """
                UPDATE vuln_scans
                SET status = 'completed', findings_count = ?, summary = ?, finished_at = CURRENT_TIMESTAMP
                WHERE scan_id = ?
                """,
                (findings_count, summary, scan_id),
            )
            row = db.execute("SELECT * FROM vuln_scans WHERE scan_id = ?", (scan_id,)).fetchone()
            return dict(row)

    def record_vuln_finding(
        self,
        *,
        scan_id: int | None,
        endpoint_id: str,
        cve_id: str,
        title: str,
        severity: float,
        port: int,
        service: str,
        remediation: str,
        status: str = "open",
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO vuln_findings (
                    scan_id, endpoint_id, cve_id, title, severity, port, service, status, remediation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (scan_id, endpoint_id, cve_id, title, severity, port, service, status, remediation),
            )
            row = db.execute("SELECT * FROM vuln_findings ORDER BY finding_id DESC LIMIT 1").fetchone()
            return dict(row)

    def list_vuln_findings(
        self,
        *,
        limit: int = 50,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        with self.connect() as db:
            if status:
                rows = db.execute(
                    "SELECT * FROM vuln_findings WHERE status = ? ORDER BY severity DESC, finding_id DESC LIMIT ?",
                    (status, limit),
                )
            else:
                rows = db.execute(
                    "SELECT * FROM vuln_findings ORDER BY severity DESC, finding_id DESC LIMIT ?",
                    (limit,),
                )
            return [dict(row) for row in rows]

    def list_vuln_scans(self, *, limit: int = 10) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM vuln_scans ORDER BY scan_id DESC LIMIT ?", (limit,))
            return [dict(row) for row in rows]

    def vuln_summary(self) -> dict[str, Any]:
        with self.connect() as db:
            open_count = db.execute("SELECT COUNT(*) FROM vuln_findings WHERE status = 'open'").fetchone()[0]
            critical = db.execute(
                "SELECT COUNT(*) FROM vuln_findings WHERE status = 'open' AND severity >= 9"
            ).fetchone()[0]
            last_scan = db.execute("SELECT * FROM vuln_scans ORDER BY scan_id DESC LIMIT 1").fetchone()
            return {
                "open_findings": open_count,
                "critical_open": critical,
                "last_scan": dict(last_scan) if last_scan else None,
            }

    def record_threat_feed_sync(self, feed_name: str, indicators_added: int, **details: Any) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO threat_feed_sync (feed_name, indicators_added, details) VALUES (?, ?, ?)",
                (feed_name, indicators_added, json.dumps(details, sort_keys=True)),
            )

    def ensure_soar_playbooks(self) -> None:
        from .soar.playbooks import DEFAULT_PLAYBOOKS, playbook_config

        with self.connect() as db:
            for playbook in DEFAULT_PLAYBOOKS:
                db.execute(
                    """
                    INSERT OR IGNORE INTO soar_playbooks (playbook_id, name, trigger_type, enabled, config)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        playbook.playbook_id,
                        playbook.name,
                        playbook.trigger,
                        int(playbook.enabled),
                        json.dumps(playbook_config(playbook.playbook_id), sort_keys=True),
                    ),
                )

    def record_soar_run(
        self,
        *,
        playbook_id: str,
        endpoint_id: str,
        trigger_ref: dict[str, Any],
        actions: list[str],
        status: str,
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO soar_runs (playbook_id, endpoint_id, status, actions, trigger_ref)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    playbook_id,
                    endpoint_id,
                    status,
                    json.dumps(actions, sort_keys=True),
                    json.dumps(trigger_ref, sort_keys=True, default=str),
                ),
            )
            row = db.execute("SELECT * FROM soar_runs ORDER BY run_id DESC LIMIT 1").fetchone()
            data = dict(row)
            data["actions"] = self._decode_json(data["actions"], [])
            data["trigger_ref"] = self._decode_json(data["trigger_ref"], {})
            return data

    def list_soar_runs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM soar_runs ORDER BY run_id DESC LIMIT ?", (limit,))
            results = []
            for row in rows:
                data = dict(row)
                data["actions"] = self._decode_json(data["actions"], [])
                data["trigger_ref"] = self._decode_json(data["trigger_ref"], {})
                results.append(data)
            return results

    def soar_summary(self) -> dict[str, Any]:
        with self.connect() as db:
            total = db.execute("SELECT COUNT(*) FROM soar_runs").fetchone()[0]
            recent = self.list_soar_runs(limit=5)
            return {"total_runs": total, "recent_runs": recent}

    def save_security_posture(self, *, score: int, grade: str, breakdown: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                "INSERT INTO security_posture (score, grade, breakdown) VALUES (?, ?, ?)",
                (score, grade, json.dumps(breakdown, sort_keys=True)),
            )
            row = db.execute("SELECT * FROM security_posture ORDER BY posture_id DESC LIMIT 1").fetchone()
            data = dict(row)
            data["breakdown"] = self._decode_json(data["breakdown"], {})
            return data

    def latest_security_posture(self) -> dict[str, Any]:
        with self.connect() as db:
            row = db.execute("SELECT * FROM security_posture ORDER BY posture_id DESC LIMIT 1").fetchone()
            if row is None:
                return {"score": 0, "grade": "-", "breakdown": {}}
            data = dict(row)
            data["breakdown"] = self._decode_json(data["breakdown"], {})
            return data

    def record_scheduler_run(self, job_name: str, status: str, details: dict[str, Any]) -> None:
        with self.connect() as db:
            db.execute(
                "INSERT INTO scheduler_runs (job_name, status, details) VALUES (?, ?, ?)",
                (job_name, status, json.dumps(details, sort_keys=True, default=str)),
            )

    def scheduler_summary(self) -> dict[str, Any]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT job_name, status, created_at FROM scheduler_runs ORDER BY run_id DESC LIMIT 8"
            )
            return {"recent_jobs": [dict(row) for row in rows]}

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

    def ensure_siem_rules(self, rules: list[dict[str, Any]]) -> int:
        inserted = 0
        with self.connect() as db:
            for rule in rules:
                cursor = db.execute(
                    """
                    INSERT OR IGNORE INTO siem_rules (
                        rule_id, name, description, condition_json, severity, enabled
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(rule["rule_id"]),
                        str(rule["name"]),
                        str(rule.get("description", "")),
                        json.dumps(rule.get("condition", {}), sort_keys=True),
                        int(rule.get("severity", 50)),
                        int(rule.get("enabled", True)),
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def create_siem_alert(
        self,
        *,
        rule_id: str,
        title: str,
        severity: int,
        endpoint_id: str = "",
        event_ids: list[int] | None = None,
        details: dict[str, Any] | None = None,
        tenant_id: str = "default",
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO siem_alerts (rule_id, title, severity, endpoint_id, event_ids, details, tenant_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rule_id,
                    title,
                    severity,
                    endpoint_id,
                    json.dumps(event_ids or [], sort_keys=True),
                    json.dumps(details or {}, sort_keys=True),
                    tenant_id,
                ),
            )
            row = db.execute("SELECT * FROM siem_alerts ORDER BY alert_id DESC LIMIT 1").fetchone()
            return self._decode_siem_alert(row)

    def list_siem_alerts(
        self, *, limit: int = 50, status: str | None = None, tenant_id: str | None = None
    ) -> list[dict[str, Any]]:
        with self.connect() as db:
            query = "SELECT * FROM siem_alerts"
            params: list[Any] = []
            clauses: list[str] = []
            if status:
                clauses.append("status = ?")
                params.append(status)
            if tenant_id:
                clauses.append("tenant_id = ?")
                params.append(tenant_id)
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            query += " ORDER BY alert_id DESC LIMIT ?"
            params.append(limit)
            rows = db.execute(query, tuple(params))
            return [self._decode_siem_alert(row) for row in rows]

    def siem_summary(self) -> dict[str, Any]:
        with self.connect() as db:
            open_alerts = db.execute(
                "SELECT COUNT(*) FROM siem_alerts WHERE status = 'open'"
            ).fetchone()[0]
            critical = db.execute(
                "SELECT COUNT(*) FROM siem_alerts WHERE status = 'open' AND severity >= 80"
            ).fetchone()[0]
            rules = db.execute("SELECT COUNT(*) FROM siem_rules WHERE enabled = 1").fetchone()[0]
        return {"open_alerts": open_alerts, "critical_alerts": critical, "enabled_rules": rules}

    def create_incident(
        self,
        *,
        incident_id: str,
        title: str,
        severity: str = "medium",
        endpoint_id: str = "",
        summary: str = "",
        assignee: str = "soc-team",
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT OR IGNORE INTO incidents (
                    incident_id, title, severity, status, assignee, endpoint_id, summary
                ) VALUES (?, ?, ?, 'open', ?, ?, ?)
                """,
                (incident_id, title, severity, assignee, endpoint_id, summary),
            )
            row = db.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)).fetchone()
            return dict(row)

    def add_incident_timeline(
        self, *, incident_id: str, entry_type: str, message: str, payload: dict[str, Any] | None = None
    ) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO incident_timeline (incident_id, entry_type, message, payload)
                VALUES (?, ?, ?, ?)
                """,
                (incident_id, entry_type, message, json.dumps(payload or {}, sort_keys=True)),
            )
            db.execute(
                "UPDATE incidents SET updated_at = CURRENT_TIMESTAMP WHERE incident_id = ?",
                (incident_id,),
            )

    def list_incidents(
        self, *, limit: int = 30, status: str | None = None, tenant_id: str | None = None
    ) -> list[dict[str, Any]]:
        with self.connect() as db:
            query = "SELECT * FROM incidents"
            params: list[Any] = []
            clauses: list[str] = []
            if status:
                clauses.append("status = ?")
                params.append(status)
            if tenant_id:
                clauses.append("tenant_id = ?")
                params.append(tenant_id)
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            query += " ORDER BY updated_at DESC LIMIT ?"
            params.append(limit)
            rows = db.execute(query, tuple(params))
            return [dict(row) for row in rows]

    def get_incident_timeline(self, incident_id: str) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM incident_timeline WHERE incident_id = ? ORDER BY entry_id",
                (incident_id,),
            )
            return [self._decode_timeline(row) for row in rows]

    def update_incident_status(self, incident_id: str, status: str) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                "UPDATE incidents SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE incident_id = ?",
                (status, incident_id),
            )
            row = db.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,)).fetchone()
            return dict(row)

    def ensure_compliance_controls(self, controls: list[dict[str, Any]]) -> int:
        inserted = 0
        with self.connect() as db:
            for ctrl in controls:
                cursor = db.execute(
                    """
                    INSERT OR IGNORE INTO compliance_controls (
                        control_id, framework, name, category, weight
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(ctrl["control_id"]),
                        str(ctrl["framework"]),
                        str(ctrl["name"]),
                        str(ctrl.get("category", "")),
                        int(ctrl.get("weight", 1)),
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def save_compliance_score(
        self, *, framework: str, score: int, passed: int, total: int, breakdown: dict[str, Any]
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO compliance_scores (framework, score, passed, total, breakdown)
                VALUES (?, ?, ?, ?, ?)
                """,
                (framework, score, passed, total, json.dumps(breakdown, sort_keys=True)),
            )
            row = db.execute("SELECT * FROM compliance_scores ORDER BY score_id DESC LIMIT 1").fetchone()
            data = dict(row)
            data["breakdown"] = self._decode_json(data["breakdown"], {})
            return data

    def latest_compliance_score(self, framework: str = "NIST-CSF") -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM compliance_scores WHERE framework = ? ORDER BY score_id DESC LIMIT 1",
                (framework,),
            ).fetchone()
            if not row:
                return None
            data = dict(row)
            data["breakdown"] = self._decode_json(data["breakdown"], {})
            return data

    def record_edr_detection(
        self,
        *,
        endpoint_id: str,
        detection_type: str,
        severity: int,
        title: str,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO edr_detections (endpoint_id, detection_type, severity, title, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    endpoint_id,
                    detection_type,
                    severity,
                    title,
                    json.dumps(details or {}, sort_keys=True),
                ),
            )
            row = db.execute("SELECT * FROM edr_detections ORDER BY detection_id DESC LIMIT 1").fetchone()
            return self._decode_edr_detection(row)

    def list_edr_detections(self, *, limit: int = 40, status: str = "open") -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM edr_detections WHERE status = ? ORDER BY detection_id DESC LIMIT ?",
                (status, limit),
            )
            return [self._decode_edr_detection(row) for row in rows]

    def record_network_flows(self, endpoint_id: str, flows: list[dict[str, Any]]) -> int:
        count = 0
        with self.connect() as db:
            for flow in flows[:100]:
                db.execute(
                    """
                    INSERT INTO network_flows (
                        endpoint_id, protocol, local_addr, remote_addr, state, risk
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        endpoint_id,
                        str(flow.get("protocol", "tcp")),
                        str(flow.get("local_addr", "")),
                        str(flow.get("remote_addr", "")),
                        str(flow.get("state", "")),
                        int(flow.get("risk", 0)),
                    ),
                )
                count += 1
        return count

    def list_network_flows(self, *, endpoint_id: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as db:
            if endpoint_id:
                rows = db.execute(
                    """
                    SELECT * FROM network_flows WHERE endpoint_id = ?
                    ORDER BY flow_id DESC LIMIT ?
                    """,
                    (endpoint_id, limit),
                )
            else:
                rows = db.execute(
                    "SELECT * FROM network_flows ORDER BY flow_id DESC LIMIT ?",
                    (limit,),
                )
            return [dict(row) for row in rows]

    def ingest_log_record(
        self,
        *,
        source: str,
        message: str,
        host: str = "",
        facility: str = "",
        severity: int = 30,
        endpoint_id: str = "",
        raw: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO log_records (
                    source, host, facility, severity, message, raw, endpoint_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source,
                    host,
                    facility,
                    severity,
                    message,
                    raw or message,
                    endpoint_id,
                    json.dumps(metadata or {}, sort_keys=True),
                ),
            )
            row = db.execute("SELECT * FROM log_records ORDER BY log_id DESC LIMIT 1").fetchone()
            data = dict(row)
            data["metadata"] = self._decode_json(data["metadata"], {})
            return data

    def search_logs(self, *, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as db:
            if query.strip():
                pattern = f"%{query.strip()}%"
                rows = db.execute(
                    """
                    SELECT * FROM log_records
                    WHERE message LIKE ? OR host LIKE ? OR source LIKE ?
                    ORDER BY log_id DESC LIMIT ?
                    """,
                    (pattern, pattern, pattern, limit),
                )
            else:
                rows = db.execute(
                    "SELECT * FROM log_records ORDER BY log_id DESC LIMIT ?",
                    (limit,),
                )
            results = []
            for row in rows:
                data = dict(row)
                data["metadata"] = self._decode_json(data["metadata"], {})
                results.append(data)
            return results

    def logvault_summary(self) -> dict[str, Any]:
        with self.connect() as db:
            total = db.execute("SELECT COUNT(*) FROM log_records").fetchone()[0]
            sources = [
                dict(row)
                for row in db.execute(
                    "SELECT source, COUNT(*) AS count FROM log_records GROUP BY source ORDER BY count DESC"
                )
            ]
        return {"total_logs": total, "by_source": sources}

    def record_suricata_alert(self, alert: dict[str, Any]) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO suricata_alerts (
                    signature_id, signature, category, severity, src_ip, dest_ip,
                    proto, mitre_technique, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(alert.get("signature_id", 0)),
                    str(alert.get("signature", "unknown")),
                    str(alert.get("category", "")),
                    int(alert.get("severity", 50)),
                    str(alert.get("src_ip", "")),
                    str(alert.get("dest_ip", "")),
                    str(alert.get("proto", "")),
                    str(alert.get("mitre_technique", "")),
                    json.dumps(alert.get("payload", {}), sort_keys=True),
                ),
            )
            row = db.execute("SELECT * FROM suricata_alerts ORDER BY alert_id DESC LIMIT 1").fetchone()
            return self._decode_suricata(row)

    def list_suricata_alerts(self, *, limit: int = 50, status: str = "open") -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM suricata_alerts WHERE status = ? ORDER BY alert_id DESC LIMIT ?",
                (status, limit),
            )
            return [self._decode_suricata(row) for row in rows]

    def create_xdr_finding(
        self,
        *,
        title: str,
        severity: int,
        endpoint_id: str = "",
        sources: list[str] | None = None,
        mitre_techniques: list[str] | None = None,
        recommended_action: str = "investigate",
        details: dict[str, Any] | None = None,
        confidence: float = 0.8,
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO xdr_findings (
                    title, severity, confidence, endpoint_id, sources, mitre_techniques,
                    recommended_action, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    severity,
                    confidence,
                    endpoint_id,
                    json.dumps(sources or [], sort_keys=True),
                    json.dumps(mitre_techniques or [], sort_keys=True),
                    recommended_action,
                    json.dumps(details or {}, sort_keys=True),
                ),
            )
            row = db.execute("SELECT * FROM xdr_findings ORDER BY finding_id DESC LIMIT 1").fetchone()
            return self._decode_xdr(row)

    def list_xdr_findings(self, *, limit: int = 30, status: str = "open") -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM xdr_findings WHERE status = ? ORDER BY finding_id DESC LIMIT ?",
                (status, limit),
            )
            return [self._decode_xdr(row) for row in rows]

    def xdr_summary(self) -> dict[str, Any]:
        with self.connect() as db:
            open_count = db.execute(
                "SELECT COUNT(*) FROM xdr_findings WHERE status = 'open'"
            ).fetchone()[0]
            critical = db.execute(
                "SELECT COUNT(*) FROM xdr_findings WHERE status = 'open' AND severity >= 85"
            ).fetchone()[0]
        return {"open_findings": open_count, "critical_open": critical}

    def ensure_yara_rules(self, rules: list[dict[str, Any]]) -> int:
        inserted = 0
        with self.connect() as db:
            for rule in rules:
                cursor = db.execute(
                    """
                    INSERT OR IGNORE INTO yara_rules (
                        rule_id, name, pattern, target, severity, mitre_technique, enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(rule["rule_id"]),
                        str(rule["name"]),
                        str(rule["pattern"]),
                        str(rule.get("target", "process")),
                        int(rule.get("severity", 70)),
                        str(rule.get("mitre_technique", "")),
                        int(rule.get("enabled", True)),
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def list_yara_rules(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM yara_rules WHERE enabled = 1")]

    @staticmethod
    def _decode_suricata(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = Database._decode_json(data["payload"], {})
        return data

    @staticmethod
    def _decode_xdr(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["sources"] = Database._decode_json(data["sources"], [])
        data["mitre_techniques"] = Database._decode_json(data["mitre_techniques"], [])
        data["details"] = Database._decode_json(data["details"], {})
        return data

    @staticmethod
    def _decode_siem_alert(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["event_ids"] = Database._decode_json(data["event_ids"], [])
        data["details"] = Database._decode_json(data["details"], {})
        return data

    @staticmethod
    def _decode_timeline(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = Database._decode_json(data["payload"], {})
        return data

    @staticmethod
    def _decode_edr_detection(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["details"] = Database._decode_json(data["details"], {})
        return data

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

    # --- v6 Global Platform ---

    def ensure_default_tenant(self) -> None:
        with self.connect() as db:
            from .migrations_v6 import apply_v6_migrations

            apply_v6_migrations(db)

    def ensure_rbac_seed(self) -> None:
        import os

        from .rbac.engine import RbacEngine

        self.ensure_default_tenant()
        with self.connect() as db:
            row = db.execute(
                "SELECT COUNT(*) FROM rbac_users WHERE tenant_id = 'default'"
            ).fetchone()[0]
            if row:
                return
            password = os.environ.get("MERSAL_ADMIN_PASSWORD", "mersal")
            pwd_hash = RbacEngine(self).hash_password(password)
            db.execute(
                """
                INSERT INTO rbac_users (user_id, tenant_id, username, password_hash, role, display_name)
                VALUES ('user-admin', 'default', 'admin', ?, 'super_admin', 'SOC Administrator')
                """,
                (pwd_hash,),
            )

    def get_rbac_user(self, username: str, *, tenant_id: str = "default") -> dict[str, Any] | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM rbac_users WHERE tenant_id = ? AND username = ?",
                (tenant_id, username),
            ).fetchone()
            return dict(row) if row else None

    def list_rbac_users(self, *, tenant_id: str | None = None) -> list[dict[str, Any]]:
        with self.connect() as db:
            if tenant_id:
                rows = db.execute("SELECT * FROM rbac_users WHERE tenant_id = ?", (tenant_id,)).fetchall()
            else:
                rows = db.execute("SELECT * FROM rbac_users ORDER BY username").fetchall()
            return [dict(row) for row in rows]

    def create_tenant(
        self,
        *,
        tenant_id: str,
        name: str,
        slug: str,
        plan: str = "enterprise",
        region: str = "global",
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO tenants (tenant_id, name, slug, plan, region)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tenant_id, name, slug, plan, region),
            )
            row = db.execute("SELECT * FROM tenants WHERE tenant_id = ?", (tenant_id,)).fetchone()
            return dict(row)

    def list_tenants(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM tenants ORDER BY name").fetchall()]

    def ensure_window_rules(self, rules: list[dict[str, Any]]) -> int:
        inserted = 0
        with self.connect() as db:
            for rule in rules:
                cursor = db.execute(
                    """
                    INSERT OR IGNORE INTO siem_window_rules (
                        rule_id, name, window_seconds, threshold, event_type, action_filter, severity, enabled
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        rule["rule_id"],
                        rule["name"],
                        int(rule.get("window_seconds", 300)),
                        int(rule.get("threshold", 5)),
                        rule.get("event_type", "*"),
                        rule.get("action_filter", "*"),
                        int(rule.get("severity", 60)),
                        int(rule.get("enabled", 1)),
                    ),
                )
                inserted += cursor.rowcount
        return inserted

    def list_window_rules(self) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM siem_window_rules WHERE enabled = 1").fetchall()]

    def count_events_in_window(
        self,
        *,
        endpoint_id: str,
        window_seconds: int,
        event_type: str = "*",
        action_filter: str = "*",
    ) -> int:
        with self.connect() as db:
            query = """
                SELECT COUNT(*) FROM events
                WHERE endpoint_id = ?
                AND datetime(created_at) >= datetime('now', ?)
            """
            params: list[Any] = [endpoint_id, f"-{int(window_seconds)} seconds"]
            if event_type != "*":
                query += " AND event_type = ?"
                params.append(event_type)
            if action_filter != "*":
                query += " AND action = ?"
                params.append(action_filter)
            return int(db.execute(query, params).fetchone()[0])

    def count_log_records(self) -> int:
        with self.connect() as db:
            return int(db.execute("SELECT COUNT(*) FROM log_records").fetchone()[0])

    def upsert_threat_indicator(
        self,
        *,
        indicator: str,
        ioc_type: str = "domain",
        severity: int = 50,
        source: str = "mersal",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO threat_intel_cache (indicator, ioc_type, severity, source, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(indicator) DO UPDATE SET
                    severity = excluded.severity,
                    source = excluded.source,
                    metadata = excluded.metadata
                """,
                (indicator, ioc_type, severity, source, json.dumps(metadata or {}, sort_keys=True)),
            )

    def list_webhooks(self, *, tenant_id: str = "default", enabled_only: bool = False) -> list[dict[str, Any]]:
        with self.connect() as db:
            query = "SELECT * FROM webhooks WHERE tenant_id = ?"
            if enabled_only:
                query += " AND enabled = 1"
            rows = db.execute(query, (tenant_id,)).fetchall()
            result = []
            for row in rows:
                data = dict(row)
                data["events"] = self._decode_json(data.get("events", "[]"), [])
                result.append(data)
            return result

    def create_webhook(
        self,
        *,
        webhook_id: str,
        tenant_id: str,
        name: str,
        url: str,
        events: list[str],
        secret: str = "",
    ) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO webhooks (webhook_id, tenant_id, name, url, events, secret, enabled)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (webhook_id, tenant_id, name, url, json.dumps(events), secret),
            )
            row = db.execute("SELECT * FROM webhooks WHERE webhook_id = ?", (webhook_id,)).fetchone()
            data = dict(row)
            data["events"] = self._decode_json(data.get("events", "[]"), [])
            return data

    def recent_alerts_for_stream(self, *, since_id: int = 0, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM siem_alerts WHERE alert_id > ? ORDER BY alert_id ASC LIMIT ?",
                (since_id, limit),
            ).fetchall()
            return [self._decode_siem_alert(row) for row in rows]

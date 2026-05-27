"""SQLite persistence and network access control workflows."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .core import (
    AccessDecision,
    Action,
    NetworkContext,
    PolicyRule,
    PolicyScope,
    evaluate_access,
    normalize_mac,
    validate_cidr,
    validate_ip,
)
from .crypto import generate_api_key, hash_chain, policy_bundle_hash, sign_policy_bundle
from .threat import assess_threat, compute_device_trust, detect_brute_force, detect_port_scan


class Database:
    def __init__(self, path: str | Path, policy_secret: str | None = None):
        self.path = Path(path)
        self.policy_secret = policy_secret or os.environ.get("EIPG_POLICY_SECRET", "dev-policy-secret-change-me")

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
                CREATE TABLE IF NOT EXISTS zones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    trust_level INTEGER NOT NULL DEFAULT 50,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL UNIQUE,
                    hostname TEXT NOT NULL,
                    mac_address TEXT NOT NULL DEFAULT '',
                    ip_address TEXT NOT NULL DEFAULT '',
                    zone TEXT NOT NULL DEFAULT 'default',
                    owner TEXT NOT NULL DEFAULT '',
                    device_type TEXT NOT NULL DEFAULT 'workstation',
                    trust_score INTEGER NOT NULL DEFAULT 50,
                    posture_compliant INTEGER NOT NULL DEFAULT 0,
                    attestation_verified INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'pending',
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    action TEXT NOT NULL DEFAULT 'deny',
                    priority INTEGER NOT NULL DEFAULT 100,
                    scope TEXT NOT NULL DEFAULT 'global',
                    source_cidr TEXT,
                    destination_cidr TEXT,
                    destination_ports TEXT,
                    protocols TEXT,
                    zones TEXT,
                    time_window TEXT,
                    min_trust_score INTEGER NOT NULL DEFAULT 0,
                    min_threat_score INTEGER NOT NULL DEFAULT 0,
                    max_threat_score INTEGER NOT NULL DEFAULT 100,
                    tags_required TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS blocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    target_type TEXT NOT NULL DEFAULT 'ip',
                    reason TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'manual',
                    severity INTEGER NOT NULL DEFAULT 50,
                    expires_at TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT NOT NULL DEFAULT 'system'
                );

                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    source_ip TEXT NOT NULL DEFAULT '',
                    destination_ip TEXT NOT NULL DEFAULT '',
                    severity INTEGER NOT NULL DEFAULT 10,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    device_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_ip TEXT NOT NULL,
                    destination_ip TEXT NOT NULL DEFAULT '',
                    destination_port INTEGER NOT NULL DEFAULT 0,
                    protocol TEXT NOT NULL DEFAULT 'tcp',
                    action TEXT NOT NULL,
                    allowed INTEGER NOT NULL,
                    reason TEXT NOT NULL,
                    matched_rule_id INTEGER,
                    trust_score INTEGER NOT NULL DEFAULT 0,
                    threat_score INTEGER NOT NULL DEFAULT 0,
                    device_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS audit_chain (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL DEFAULT 'system',
                    payload_json TEXT NOT NULL,
                    chain_hash TEXT NOT NULL UNIQUE,
                    previous_hash TEXT NOT NULL DEFAULT 'genesis',
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

                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'agent',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS policy_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version INTEGER NOT NULL UNIQUE,
                    rules_hash TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def seed_demo(self) -> None:
        with self.connect() as db:
            if db.execute("SELECT COUNT(*) FROM zones").fetchone()[0] == 0:
                db.executemany(
                    "INSERT INTO zones (name, description, trust_level) VALUES (?, ?, ?)",
                    [
                        ("default", "General corporate network", 50),
                        ("dmz", "Demilitarized zone — external-facing services", 30),
                        ("secure", "High-security internal segment", 80),
                        ("guest", "Guest Wi-Fi isolation zone", 10),
                        ("iot", "IoT device micro-segment", 20),
                    ],
                )
            if db.execute("SELECT COUNT(*) FROM policies").fetchone()[0] == 0:
                db.executemany(
                    """
                    INSERT INTO policies
                        (name, action, priority, scope, source_cidr, destination_cidr,
                         destination_ports, protocols, zones, min_trust_score, min_threat_score, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            "Block critical threats",
                            "deny",
                            1000,
                            "global",
                            None,
                            None,
                            None,
                            None,
                            None,
                            0,
                            75,
                            "Auto-deny when threat score exceeds threshold",
                        ),
                        (
                            "Allow secure zone internal",
                            "allow",
                            500,
                            "zone",
                            "10.0.0.0/8",
                            "10.0.0.0/8",
                            None,
                            "tcp,udp,icmp",
                            "secure",
                            60,
                            0,
                            "Internal traffic within secure micro-segment",
                        ),
                        (
                            "Allow HTTPS outbound",
                            "allow",
                            300,
                            "global",
                            "10.0.0.0/8",
                            "0.0.0.0/0",
                            "443",
                            "tcp",
                            None,
                            40,
                            0,
                            "Standard HTTPS egress for registered devices",
                        ),
                        (
                            "Allow DNS",
                            "allow",
                            350,
                            "global",
                            "10.0.0.0/8",
                            None,
                            "53",
                            "udp,tcp",
                            None,
                            30,
                            0,
                            "DNS resolution for corporate clients",
                        ),
                        (
                            "Quarantine guest zone",
                            "quarantine",
                            400,
                            "zone",
                            None,
                            None,
                            None,
                            None,
                            "guest",
                            0,
                            0,
                            "Guest devices require captive portal verification",
                        ),
                        (
                            "Deny IoT lateral movement",
                            "deny",
                            450,
                            "zone",
                            None,
                            "10.0.0.0/8",
                            None,
                            "tcp,udp",
                            "iot",
                            0,
                            0,
                            "IoT devices cannot reach internal corporate network",
                        ),
                        (
                            "Default deny all",
                            "deny",
                            1,
                            "global",
                            None,
                            None,
                            None,
                            None,
                            None,
                            0,
                            0,
                            "Zero-trust default deny — explicit allow required",
                        ),
                    ],
                )
            if db.execute("SELECT COUNT(*) FROM devices").fetchone()[0] == 0:
                db.executemany(
                    """
                    INSERT INTO devices
                        (device_id, hostname, mac_address, ip_address, zone, owner,
                         device_type, trust_score, posture_compliant, attestation_verified, status, tags_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            "dev-laptop-001",
                            "LAPTOP-001",
                            "aa:bb:cc:dd:ee:01",
                            "10.0.1.50",
                            "secure",
                            "ahmed.admin",
                            "workstation",
                            85,
                            1,
                            1,
                            "approved",
                            '["corporate", "managed"]',
                        ),
                        (
                            "dev-server-001",
                            "SRV-DB-01",
                            "aa:bb:cc:dd:ee:02",
                            "10.0.2.10",
                            "secure",
                            "it.ops",
                            "server",
                            90,
                            1,
                            1,
                            "approved",
                            '["server", "critical"]',
                        ),
                        (
                            "dev-guest-001",
                            "GUEST-PHONE",
                            "aa:bb:cc:dd:ee:03",
                            "192.168.100.55",
                            "guest",
                            "visitor",
                            "mobile",
                            15,
                            0,
                            0,
                            "pending",
                            '["guest"]',
                        ),
                        (
                            "dev-iot-001",
                            "CAM-LOBBY",
                            "aa:bb:cc:dd:ee:04",
                            "10.0.5.20",
                            "iot",
                            "facilities",
                            "camera",
                            25,
                            1,
                            0,
                            "approved",
                            '["iot", "camera"]',
                        ),
                    ],
                )
            if db.execute("SELECT COUNT(*) FROM blocks").fetchone()[0] == 0:
                db.executemany(
                    """
                    INSERT INTO blocks (target, target_type, reason, source, severity, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            "203.0.113.50",
                            "ip",
                            "Known C2 server — threat intelligence feed",
                            "threat-intel",
                            90,
                            "system",
                        ),
                        (
                            "198.51.100.0/24",
                            "cidr",
                            "Suspicious ASN block",
                            "threat-intel",
                            70,
                            "system",
                        ),
                    ],
                )
            self._publish_policy_version(db)

    def list_zones(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM zones ORDER BY name")

    def list_devices(self) -> list[dict[str, Any]]:
        devices = self._fetch_all("SELECT * FROM devices ORDER BY last_seen DESC")
        for device in devices:
            device["tags"] = json.loads(device.pop("tags_json") or "[]")
            device["metadata"] = json.loads(device.pop("metadata_json") or "{}")
        return devices

    def list_policies(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM policies ORDER BY priority DESC")

    def list_blocks(self, active_only: bool = True) -> list[dict[str, Any]]:
        sql = "SELECT * FROM blocks"
        if active_only:
            sql += " WHERE is_active = 1 AND (expires_at IS NULL OR expires_at > datetime('now'))"
        sql += " ORDER BY created_at DESC"
        return self._fetch_all(sql)

    def list_events(self, limit: int = 100) -> list[dict[str, Any]]:
        events = self._fetch_all(
            "SELECT * FROM security_events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        for event in events:
            event["details"] = json.loads(event.pop("details_json") or "{}")
        return events

    def list_access_log(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM access_log ORDER BY id DESC LIMIT ?", (limit,))

    def list_agents(self) -> list[dict[str, Any]]:
        agents = self._fetch_all("SELECT * FROM agents ORDER BY last_seen DESC")
        for agent in agents:
            agent["metadata"] = json.loads(agent.pop("metadata_json") or "{}")
        return agents

    def list_audit(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._fetch_all("SELECT * FROM audit_chain ORDER BY id DESC LIMIT ?", (limit,))
        for row in rows:
            row["payload"] = json.loads(row.pop("payload_json") or "{}")
        return rows

    def register_device(
        self,
        *,
        device_id: str,
        hostname: str,
        mac_address: str = "",
        ip_address: str = "",
        zone: str = "default",
        owner: str = "",
        device_type: str = "workstation",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        device_id = device_id.strip()
        if not device_id:
            raise ValueError("device_id is required")
        if ip_address:
            ip_address = validate_ip(ip_address)
        if mac_address:
            mac_address = normalize_mac(mac_address)

        with self.connect() as db:
            db.execute(
                """
                INSERT INTO devices
                    (device_id, hostname, mac_address, ip_address, zone, owner, device_type, tags_json, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                ON CONFLICT(device_id) DO UPDATE SET
                    hostname = excluded.hostname,
                    mac_address = CASE WHEN excluded.mac_address != '' THEN excluded.mac_address ELSE devices.mac_address END,
                    ip_address = CASE WHEN excluded.ip_address != '' THEN excluded.ip_address ELSE devices.ip_address END,
                    zone = excluded.zone,
                    owner = excluded.owner,
                    device_type = excluded.device_type,
                    tags_json = excluded.tags_json,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (
                    device_id,
                    hostname.strip(),
                    mac_address,
                    ip_address,
                    zone,
                    owner,
                    device_type,
                    json.dumps(tags or [], sort_keys=True),
                ),
            )
            device = self._get_device_dict(db, device_id)
            self._audit(db, "device.register", "api", {"device_id": device_id, "hostname": hostname})
            return device

    def approve_device(self, device_id: str) -> dict[str, Any]:
        with self.connect() as db:
            db.execute(
                "UPDATE devices SET status = 'approved', trust_score = MAX(trust_score, 60) WHERE device_id = ?",
                (device_id,),
            )
            device = self._get_device_dict(db, device_id)
            self._audit(db, "device.approve", "admin", {"device_id": device_id})
            return device

    def create_policy(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = str(payload["name"]).strip()
        if not name:
            raise ValueError("policy name is required")
        action = str(payload.get("action", "deny")).lower()
        if action not in {a.value for a in Action}:
            raise ValueError(f"invalid action: {action}")

        with self.connect() as db:
            cursor = db.execute(
                """
                INSERT INTO policies
                    (name, action, priority, scope, source_cidr, destination_cidr,
                     destination_ports, protocols, zones, time_window, min_trust_score,
                     min_threat_score, max_threat_score, tags_required, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    action,
                    int(payload.get("priority", 100)),
                    str(payload.get("scope", "global")),
                    payload.get("source_cidr"),
                    payload.get("destination_cidr"),
                    payload.get("destination_ports"),
                    payload.get("protocols"),
                    payload.get("zones"),
                    payload.get("time_window"),
                    int(payload.get("min_trust_score", 0)),
                    int(payload.get("min_threat_score", 0)),
                    int(payload.get("max_threat_score", 100)),
                    payload.get("tags_required"),
                    str(payload.get("description", "")),
                ),
            )
            policy = self._row_to_dict(db.execute("SELECT * FROM policies WHERE id = ?", (cursor.lastrowid,)).fetchone())
            self._publish_policy_version(db)
            self._audit(db, "policy.create", "admin", {"policy_id": policy["id"], "name": name})
            return policy

    def create_block(
        self,
        *,
        target: str,
        target_type: str = "ip",
        reason: str,
        source: str = "manual",
        severity: int = 50,
        ttl_hours: int | None = None,
        created_by: str = "admin",
    ) -> dict[str, Any]:
        target = target.strip()
        if not target:
            raise ValueError("block target is required")
        if target_type == "ip":
            target = validate_ip(target)
        elif target_type == "cidr":
            target = validate_cidr(target)

        expires_at = None
        if ttl_hours:
            expires = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
            expires_at = expires.strftime("%Y-%m-%d %H:%M:%S")

        with self.connect() as db:
            cursor = db.execute(
                """
                INSERT INTO blocks (target, target_type, reason, source, severity, expires_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (target, target_type, reason, source, severity, expires_at, created_by),
            )
            block = self._row_to_dict(db.execute("SELECT * FROM blocks WHERE id = ?", (cursor.lastrowid,)).fetchone())
            self._audit(db, "block.create", created_by, {"target": target, "reason": reason})
            return block

    def record_event(
        self,
        *,
        event_type: str,
        source_ip: str = "",
        destination_ip: str = "",
        severity: int = 10,
        details: dict[str, Any] | None = None,
        device_id: str | None = None,
    ) -> dict[str, Any]:
        with self.connect() as db:
            cursor = db.execute(
                """
                INSERT INTO security_events
                    (event_type, source_ip, destination_ip, severity, details_json, device_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_type,
                    source_ip,
                    destination_ip,
                    severity,
                    json.dumps(details or {}, sort_keys=True),
                    device_id,
                ),
            )
            event = self._row_to_dict(
                db.execute("SELECT * FROM security_events WHERE id = ?", (cursor.lastrowid,)).fetchone()
            )
            event["details"] = json.loads(event.pop("details_json") or "{}")

            if source_ip:
                recent = self._recent_events_for_ip(db, source_ip)
                assessment = assess_threat(recent_events=recent)
                if assessment.auto_block:
                    existing = db.execute(
                        "SELECT id FROM blocks WHERE target = ? AND is_active = 1",
                        (source_ip,),
                    ).fetchone()
                    if not existing:
                        db.execute(
                            """
                            INSERT INTO blocks (target, target_type, reason, source, severity, created_by)
                            VALUES (?, 'ip', ?, 'auto-response', ?, 'system')
                            """,
                            (
                                source_ip,
                                f"Auto-block: threat score {assessment.score} ({', '.join(assessment.triggers[:3])})",
                                assessment.score,
                            ),
                        )
                        self._audit(db, "block.auto", "system", {"source_ip": source_ip, "score": assessment.score})

            return event

    def evaluate(
        self,
        *,
        source_ip: str,
        destination_ip: str = "0.0.0.0",
        destination_port: int = 0,
        protocol: str = "tcp",
        zone: str = "default",
        device_id: str | None = None,
        log: bool = True,
    ) -> dict[str, Any]:
        source_ip = validate_ip(source_ip)
        if destination_ip and destination_ip != "0.0.0.0":
            destination_ip = validate_ip(destination_ip)

        with self.connect() as db:
            block_decision = self._check_blocks(db, source_ip)
            if block_decision:
                if log:
                    self._log_access(db, block_decision, source_ip, destination_ip, destination_port, protocol, device_id)
                return block_decision.to_dict()

            device = None
            device_trust = 30
            tags: set[str] = set()
            if device_id:
                row = db.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,)).fetchone()
                if row:
                    device = self._row_to_dict(row)
                    tags = set(json.loads(device.get("tags_json") or "[]"))
                    if device["status"] != "approved":
                        decision = AccessDecision(
                            allowed=False,
                            action=Action.DENY,
                            reason=f"Device {device_id} not approved (status: {device['status']})",
                            trust_score=device["trust_score"],
                        )
                        if log:
                            self._log_access(db, decision, source_ip, destination_ip, destination_port, protocol, device_id)
                        return decision.to_dict()
                    device_trust = compute_device_trust(
                        registered=True,
                        posture_compliant=bool(device["posture_compliant"]),
                        last_seen_hours=1,
                        violation_count=0,
                        attestation_verified=bool(device["attestation_verified"]),
                    )
                    zone = device.get("zone") or zone

            recent = self._recent_events_for_ip(db, source_ip)
            threat = assess_threat(recent_events=recent)
            rules = self._load_rules(db)
            version = self._current_policy_version(db)
            ctx = NetworkContext(
                source_ip=source_ip,
                destination_ip=destination_ip,
                destination_port=destination_port,
                protocol=protocol,
                zone=zone,
                device_id=device_id,
                tags=frozenset(tags),
                threat_score=threat.score,
            )
            decision = evaluate_access(ctx, rules, policy_version=version, device_trust_score=device_trust)
            if log:
                self._log_access(db, decision, source_ip, destination_ip, destination_port, protocol, device_id)
            return decision.to_dict()

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
        if not agent_id:
            raise ValueError("agent_id is required")
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
                (agent_id, agent_type, hostname.strip(), os_name, version, metadata_json),
            )
            agent = self._row_to_dict(db.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,)).fetchone())
            agent["metadata"] = json.loads(agent.pop("metadata_json") or "{}")
            policy = self.get_policy_bundle()
            agent["policy_version"] = policy["version"]
            agent["policy_signature"] = policy["signature"]
            return agent

    def get_policy_bundle(self) -> dict[str, Any]:
        with self.connect() as db:
            version_row = db.execute("SELECT MAX(version) AS v FROM policy_versions").fetchone()
            version = version_row["v"] or 0
            rules = self.list_policies()
            bundle = {"version": version, "rules": rules, "blocks": self.list_blocks()}
            signature = sign_policy_bundle(bundle, self.policy_secret)
            return {**bundle, "signature": signature, "rules_hash": policy_bundle_hash(rules, version)}

    def ingest_flow(
        self,
        *,
        source_ip: str,
        destination_ip: str,
        destination_port: int,
        protocol: str = "tcp",
        bytes_sent: int = 0,
        packets: int = 1,
    ) -> dict[str, Any]:
        """Process flow telemetry — detect scans and evaluate access."""
        with self.connect() as db:
            window_start = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
            port_count = db.execute(
                """
                SELECT COUNT(DISTINCT destination_port) FROM access_log
                WHERE source_ip = ? AND created_at >= ?
                """,
                (source_ip, window_start),
            ).fetchone()[0]
            host_count = db.execute(
                """
                SELECT COUNT(DISTINCT destination_ip) FROM access_log
                WHERE source_ip = ? AND created_at >= ?
                """,
                (source_ip, window_start),
            ).fetchone()[0]

        scan = detect_port_scan(
            source_ip=source_ip,
            unique_ports=port_count + 1,
            unique_hosts=host_count + 1,
        )
        if scan:
            self.record_event(
                event_type=scan.event_type,
                source_ip=source_ip,
                severity=scan.severity,
                details=scan.details,
            )

        decision = self.evaluate(
            source_ip=source_ip,
            destination_ip=destination_ip,
            destination_port=destination_port,
            protocol=protocol,
            log=True,
        )
        return {"flow": {"bytes_sent": bytes_sent, "packets": packets}, "decision": decision}

    def report_brute_force(
        self,
        *,
        source_ip: str,
        target_service: str,
        failed_attempts: int,
    ) -> dict[str, Any]:
        event = detect_brute_force(
            source_ip=source_ip,
            failed_attempts=failed_attempts,
            target_service=target_service,
        )
        if event:
            return self.record_event(
                event_type=event.event_type,
                source_ip=source_ip,
                severity=event.severity,
                details=event.details,
            )
        return {"status": "below_threshold"}

    def dashboard(self) -> dict[str, Any]:
        with self.connect() as db:
            stats = self._row_to_dict(
                db.execute(
                    """
                    SELECT
                        (SELECT COUNT(*) FROM devices) AS devices,
                        (SELECT COUNT(*) FROM devices WHERE status = 'approved') AS approved_devices,
                        (SELECT COUNT(*) FROM devices WHERE status = 'pending') AS pending_devices,
                        (SELECT COUNT(*) FROM policies WHERE is_active = 1) AS policies,
                        (SELECT COUNT(*) FROM blocks WHERE is_active = 1) AS active_blocks,
                        (SELECT COUNT(*) FROM agents) AS agents,
                        (SELECT COUNT(*) FROM security_events) AS events,
                        (SELECT COUNT(*) FROM access_log WHERE allowed = 0) AS denied_access,
                        (SELECT COUNT(*) FROM access_log WHERE allowed = 1) AS allowed_access
                    """
                ).fetchone()
            )
            stats["zones"] = db.execute("SELECT COUNT(*) FROM zones").fetchone()[0]
            stats["policy_version"] = self._current_policy_version(db)
            stats["recent_threats"] = self._fetch_all(
                """
                SELECT event_type, COUNT(*) AS count
                FROM security_events
                WHERE created_at >= datetime('now', '-24 hours')
                GROUP BY event_type
                ORDER BY count DESC
                LIMIT 10
                """
            )
            stats["top_blocked_ips"] = self._fetch_all(
                """
                SELECT source_ip, COUNT(*) AS attempts
                FROM access_log
                WHERE allowed = 0
                GROUP BY source_ip
                ORDER BY attempts DESC
                LIMIT 10
                """
            )
            stats["zone_devices"] = self._fetch_all(
                """
                SELECT zone, COUNT(*) AS count, AVG(trust_score) AS avg_trust
                FROM devices
                GROUP BY zone
                ORDER BY count DESC
                """
            )
            return stats

    def generate_demo_api_key(self, name: str = "demo-agent") -> str:
        key = generate_api_key()
        key_hash = hashlib_sha256(key)
        with self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO api_keys (key_hash, name, role) VALUES (?, ?, 'agent')",
                (key_hash, name),
            )
        return key

    def _check_blocks(self, db: sqlite3.Connection, source_ip: str) -> AccessDecision | None:
        blocks = db.execute(
            """
            SELECT * FROM blocks
            WHERE is_active = 1 AND (expires_at IS NULL OR expires_at > datetime('now'))
            """
        ).fetchall()
        for block in blocks:
            target = block["target"]
            if block["target_type"] == "ip" and target == source_ip:
                return AccessDecision(
                    allowed=False,
                    action=Action.DENY,
                    reason=f"Blocked: {block['reason']}",
                    metadata={"block_id": block["id"], "source": block["source"]},
                )
            if block["target_type"] == "cidr" and _ip_in_block(source_ip, target):
                return AccessDecision(
                    allowed=False,
                    action=Action.DENY,
                    reason=f"Blocked CIDR {target}: {block['reason']}",
                    metadata={"block_id": block["id"], "source": block["source"]},
                )
        return None

    def _load_rules(self, db: sqlite3.Connection) -> list[PolicyRule]:
        rows = db.execute("SELECT * FROM policies WHERE is_active = 1").fetchall()
        rules = []
        for row in rows:
            rules.append(
                PolicyRule(
                    id=row["id"],
                    name=row["name"],
                    action=Action(row["action"]),
                    priority=row["priority"],
                    scope=PolicyScope(row["scope"]),
                    source_cidr=row["source_cidr"],
                    destination_cidr=row["destination_cidr"],
                    destination_ports=row["destination_ports"],
                    protocols=row["protocols"],
                    zones=row["zones"],
                    time_window=row["time_window"],
                    min_trust_score=row["min_trust_score"],
                    min_threat_score=row["min_threat_score"] if "min_threat_score" in row.keys() else 0,
                    max_threat_score=row["max_threat_score"],
                    tags_required=row["tags_required"],
                    is_active=bool(row["is_active"]),
                    description=row["description"] or "",
                )
            )
        return rules

    def _log_access(
        self,
        db: sqlite3.Connection,
        decision: AccessDecision,
        source_ip: str,
        destination_ip: str,
        destination_port: int,
        protocol: str,
        device_id: str | None,
    ) -> None:
        db.execute(
            """
            INSERT INTO access_log
                (source_ip, destination_ip, destination_port, protocol, action, allowed,
                 reason, matched_rule_id, trust_score, threat_score, device_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_ip,
                destination_ip,
                destination_port,
                protocol,
                decision.action.value,
                int(decision.allowed),
                decision.reason,
                decision.matched_rule_id,
                decision.trust_score,
                decision.threat_score,
                device_id,
            ),
        )

    def _recent_events_for_ip(self, db: sqlite3.Connection, source_ip: str) -> list[dict[str, Any]]:
        rows = db.execute(
            """
            SELECT event_type, severity, created_at FROM security_events
            WHERE source_ip = ? AND created_at >= datetime('now', '-1 hour')
            ORDER BY id DESC LIMIT 50
            """,
            (source_ip,),
        ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def _publish_policy_version(self, db: sqlite3.Connection) -> None:
        rules = [self._row_to_dict(row) for row in db.execute("SELECT * FROM policies WHERE is_active = 1").fetchall()]
        current = self._current_policy_version(db)
        new_version = current + 1
        rules_hash = policy_bundle_hash(rules, new_version)
        bundle = {"version": new_version, "rules": rules}
        signature = sign_policy_bundle(bundle, self.policy_secret)
        db.execute(
            "INSERT INTO policy_versions (version, rules_hash, signature) VALUES (?, ?, ?)",
            (new_version, rules_hash, signature),
        )

    def _current_policy_version(self, db: sqlite3.Connection) -> int:
        row = db.execute("SELECT MAX(version) AS v FROM policy_versions").fetchone()
        return row["v"] or 0

    def _audit(self, db: sqlite3.Connection, event_type: str, actor: str, payload: dict[str, Any]) -> None:
        previous = db.execute("SELECT chain_hash FROM audit_chain ORDER BY id DESC LIMIT 1").fetchone()
        previous_hash = previous["chain_hash"] if previous else "genesis"
        payload_json = json.dumps(payload, sort_keys=True)
        chain_hash = hash_chain(previous_hash, f"{event_type}|{actor}|{payload_json}")
        db.execute(
            """
            INSERT INTO audit_chain (event_type, actor, payload_json, chain_hash, previous_hash)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_type, actor, payload_json, chain_hash, previous_hash),
        )

    def _get_device_dict(self, db: sqlite3.Connection, device_id: str) -> dict[str, Any]:
        row = db.execute("SELECT * FROM devices WHERE device_id = ?", (device_id,)).fetchone()
        if row is None:
            raise ValueError("device not found")
        device = self._row_to_dict(row)
        device["tags"] = json.loads(device.pop("tags_json") or "[]")
        device["metadata"] = json.loads(device.pop("metadata_json") or "{}")
        return device

    def _fetch_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [self._row_to_dict(row) for row in db.execute(sql, params).fetchall()]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        return {key: row[key] for key in row.keys()}


def hashlib_sha256(value: str) -> str:
    import hashlib

    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _ip_in_block(ip: str, cidr: str) -> bool:
    import ipaddress

    try:
        return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False

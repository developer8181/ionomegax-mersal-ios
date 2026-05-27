"""SQLite persistence and workflows for Extreme IP Guard."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .core import DlpEvent, classify_ip_address, evaluate_asset_posture, evaluate_dlp_event, posture_from_dict


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
                    asset_id TEXT NOT NULL UNIQUE,
                    hostname TEXT NOT NULL,
                    owner TEXT NOT NULL DEFAULT '',
                    department TEXT NOT NULL DEFAULT 'General',
                    ip_address TEXT NOT NULL DEFAULT '',
                    ip_classification_json TEXT NOT NULL DEFAULT '{}',
                    os_name TEXT NOT NULL DEFAULT '',
                    agent_version TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'healthy',
                    risk_score INTEGER NOT NULL DEFAULT 0,
                    risk_level TEXT NOT NULL DEFAULT 'low',
                    policy_action TEXT NOT NULL DEFAULT 'allow',
                    posture_json TEXT NOT NULL DEFAULT '{}',
                    risk_reasons_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS dlp_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id INTEGER REFERENCES assets(id),
                    username TEXT NOT NULL DEFAULT '',
                    channel TEXT NOT NULL,
                    sensitivity TEXT NOT NULL,
                    destination TEXT NOT NULL DEFAULT '',
                    destination_trusted INTEGER NOT NULL DEFAULT 0,
                    bytes_count INTEGER NOT NULL DEFAULT 0,
                    encrypted INTEGER NOT NULL DEFAULT 0,
                    user_override INTEGER NOT NULL DEFAULT 0,
                    allowed INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(asset_id) REFERENCES assets(id)
                );

                CREATE TABLE IF NOT EXISTS policies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    details_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    def seed_demo(self) -> None:
        with self.connect() as db:
            policy_count = db.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
            asset_count = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            if policy_count == 0:
                db.executemany(
                    """
                    INSERT INTO policies (name, category, description)
                    VALUES (?, ?, ?)
                    """,
                    [
                        ("Zero Trust Endpoint Baseline", "endpoint", "Require encryption, EDR, firewall, and timely patching."),
                        ("Confidential Data Boundary", "dlp", "Prevent confidential data from leaving trusted destinations."),
                        ("Critical Risk Isolation", "response", "Recommend isolation for critical-risk endpoints."),
                        ("Transparent Audit", "governance", "Record administrative and automated security decisions."),
                    ],
                )
        if asset_count == 0:
            self.record_asset_heartbeat(
                asset_id="demo-laptop-001",
                hostname="future-finance-01",
                owner="Sara",
                department="Finance",
                ip_address="10.20.1.42",
                os_name="Windows 11 Enterprise",
                agent_version="0.1.0",
                posture={
                    "encryption_enabled": True,
                    "edr_enabled": True,
                    "firewall_enabled": True,
                    "os_patch_age_days": 9,
                    "critical_vulns": 0,
                    "high_vulns": 1,
                    "sensitive_data_at_rest": True,
                },
                metadata={"zone": "HQ", "consent_mode": "enterprise_notice"},
            )
            self.record_asset_heartbeat(
                asset_id="demo-server-007",
                hostname="legacy-branch-server",
                owner="IT Operations",
                department="Infrastructure",
                ip_address="203.0.113.10",
                os_name="Ubuntu Server",
                agent_version="0.1.0",
                posture={
                    "encryption_enabled": False,
                    "edr_enabled": False,
                    "firewall_enabled": True,
                    "os_patch_age_days": 104,
                    "critical_vulns": 2,
                    "high_vulns": 4,
                    "external_ip_exposure": True,
                    "unusual_egress_mb": 512,
                },
                metadata={"zone": "Branch", "service": "files"},
            )

    def dashboard(self) -> dict[str, Any]:
        with self.connect() as db:
            risk_counts = {
                row["risk_level"]: row["count"]
                for row in db.execute("SELECT risk_level, COUNT(*) AS count FROM assets GROUP BY risk_level")
            }
            dlp_counts = {
                row["action"]: row["count"]
                for row in db.execute("SELECT action, COUNT(*) AS count FROM dlp_events GROUP BY action")
            }
            totals = {
                "assets": db.execute("SELECT COUNT(*) FROM assets").fetchone()[0],
                "critical_assets": db.execute("SELECT COUNT(*) FROM assets WHERE risk_level = 'critical'").fetchone()[0],
                "dlp_events": db.execute("SELECT COUNT(*) FROM dlp_events").fetchone()[0],
                "blocked_events": db.execute("SELECT COUNT(*) FROM dlp_events WHERE allowed = 0").fetchone()[0],
            }
        return {
            "totals": totals,
            "risk_counts": risk_counts,
            "dlp_action_counts": dlp_counts,
            "recent_assets": self.list_assets(limit=8),
            "recent_dlp_events": self.list_dlp_events(limit=8),
            "policies": self.list_policies(),
        }

    def list_assets(self, limit: int = 100) -> list[dict[str, Any]]:
        assets = self._fetch_all("SELECT * FROM assets ORDER BY risk_score DESC, last_seen DESC LIMIT ?", (limit,))
        for asset in assets:
            self._expand_asset_json(asset)
        return assets

    def list_policies(self) -> list[dict[str, Any]]:
        return self._fetch_all("SELECT * FROM policies ORDER BY category, name")

    def list_dlp_events(self, limit: int = 100) -> list[dict[str, Any]]:
        events = self._fetch_all(
            """
            SELECT e.*, a.hostname AS asset_hostname
            FROM dlp_events e
            LEFT JOIN assets a ON a.id = e.asset_id
            ORDER BY e.id DESC
            LIMIT ?
            """,
            (limit,),
        )
        for event in events:
            event["destination_trusted"] = bool(event["destination_trusted"])
            event["encrypted"] = bool(event["encrypted"])
            event["user_override"] = bool(event["user_override"])
            event["allowed"] = bool(event["allowed"])
        return events

    def list_audit_log(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._fetch_all("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
        for row in rows:
            row["details"] = json.loads(row.pop("details_json") or "{}")
        return rows

    def record_asset_heartbeat(
        self,
        *,
        asset_id: str,
        hostname: str,
        owner: str = "",
        department: str = "General",
        ip_address: str = "",
        os_name: str = "",
        agent_version: str = "",
        posture: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        asset_id = asset_id.strip()
        hostname = hostname.strip()
        if not asset_id:
            raise ValueError("asset_id is required")
        if not hostname:
            raise ValueError("hostname is required")

        posture_obj = posture_from_dict(posture or {})
        risk = evaluate_asset_posture(posture_obj)
        ip_classification = classify_ip_address(ip_address) if ip_address.strip() else {}
        status = "healthy" if risk.action == "allow" else risk.action

        with self.connect() as db:
            current = db.execute("SELECT status FROM assets WHERE asset_id = ?", (asset_id,)).fetchone()
            if current and current["status"] == "isolated":
                status = "isolated"

            db.execute(
                """
                INSERT INTO assets (
                    asset_id, hostname, owner, department, ip_address, ip_classification_json,
                    os_name, agent_version, status, risk_score, risk_level, policy_action,
                    posture_json, risk_reasons_json, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET
                    hostname = excluded.hostname,
                    owner = excluded.owner,
                    department = excluded.department,
                    ip_address = excluded.ip_address,
                    ip_classification_json = excluded.ip_classification_json,
                    os_name = excluded.os_name,
                    agent_version = excluded.agent_version,
                    status = excluded.status,
                    risk_score = excluded.risk_score,
                    risk_level = excluded.risk_level,
                    policy_action = excluded.policy_action,
                    posture_json = excluded.posture_json,
                    risk_reasons_json = excluded.risk_reasons_json,
                    metadata_json = excluded.metadata_json,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (
                    asset_id,
                    hostname,
                    owner.strip(),
                    department.strip() or "General",
                    ip_address.strip(),
                    json.dumps(ip_classification, sort_keys=True),
                    os_name.strip(),
                    agent_version.strip(),
                    status,
                    risk.risk_score,
                    risk.risk_level,
                    risk.action,
                    json.dumps(asdict(posture_obj), sort_keys=True),
                    json.dumps(list(risk.reasons), sort_keys=True),
                    json.dumps(metadata or {}, sort_keys=True),
                ),
            )
            asset = self._asset_by_ref(db, asset_id)
            self._write_audit(
                db,
                actor="system",
                action="asset_heartbeat",
                target_type="asset",
                target_id=str(asset["id"]),
                details={"risk_score": risk.risk_score, "risk_level": risk.risk_level, "policy_action": risk.action},
            )
        self._expand_asset_json(asset)
        return asset

    def record_dlp_event(
        self,
        *,
        asset_ref: str | int | None,
        username: str,
        channel: str,
        sensitivity: str,
        destination: str = "",
        destination_trusted: bool = False,
        bytes_count: int = 0,
        encrypted: bool = False,
        user_override: bool = False,
    ) -> dict[str, Any]:
        event = DlpEvent(
            channel=channel,
            sensitivity=sensitivity,
            destination_trusted=destination_trusted,
            bytes_count=bytes_count,
            encrypted=encrypted,
            user_override=user_override,
        )
        decision = evaluate_dlp_event(event)

        with self.connect() as db:
            asset = self._asset_by_ref(db, asset_ref) if asset_ref not in (None, "") else None
            cursor = db.execute(
                """
                INSERT INTO dlp_events (
                    asset_id, username, channel, sensitivity, destination, destination_trusted,
                    bytes_count, encrypted, user_override, allowed, action, severity, reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    asset["id"] if asset else None,
                    username.strip(),
                    channel.strip(),
                    sensitivity.strip(),
                    destination.strip(),
                    int(destination_trusted),
                    bytes_count,
                    int(encrypted),
                    int(user_override),
                    int(decision.allowed),
                    decision.action,
                    decision.severity,
                    decision.reason,
                ),
            )
            event_id = cursor.lastrowid
            self._write_audit(
                db,
                actor=username.strip() or "system",
                action=f"dlp_{decision.action}",
                target_type="dlp_event",
                target_id=str(event_id),
                details={"allowed": decision.allowed, "severity": decision.severity, "reason": decision.reason},
            )
            row = self._get_row(
                db,
                """
                SELECT e.*, a.hostname AS asset_hostname
                FROM dlp_events e
                LEFT JOIN assets a ON a.id = e.asset_id
                WHERE e.id = ?
                """,
                (event_id,),
            )
        result = self._row_to_dict(row)
        result["destination_trusted"] = bool(result["destination_trusted"])
        result["encrypted"] = bool(result["encrypted"])
        result["user_override"] = bool(result["user_override"])
        result["allowed"] = bool(result["allowed"])
        return result

    def isolate_asset(self, asset_ref: str | int, actor: str = "admin") -> dict[str, Any]:
        return self._set_asset_status(asset_ref, "isolated", actor, "asset_isolated")

    def restore_asset(self, asset_ref: str | int, actor: str = "admin") -> dict[str, Any]:
        return self._set_asset_status(asset_ref, "healthy", actor, "asset_restored")

    def _set_asset_status(self, asset_ref: str | int, status: str, actor: str, action: str) -> dict[str, Any]:
        with self.connect() as db:
            asset = self._asset_by_ref(db, asset_ref)
            db.execute("UPDATE assets SET status = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?", (status, asset["id"]))
            self._write_audit(db, actor=actor, action=action, target_type="asset", target_id=str(asset["id"]), details={"status": status})
            updated = self._asset_by_ref(db, asset["id"])
        self._expand_asset_json(updated)
        return updated

    def _asset_by_ref(self, db: sqlite3.Connection, ref: str | int | None) -> dict[str, Any]:
        if ref is None:
            raise ValueError("asset reference is required")
        row = None
        if isinstance(ref, int) or str(ref).isdigit():
            row = db.execute("SELECT * FROM assets WHERE id = ?", (int(ref),)).fetchone()
        if row is None:
            row = db.execute("SELECT * FROM assets WHERE asset_id = ? OR hostname = ?", (str(ref), str(ref))).fetchone()
        if row is None:
            raise ValueError(f"asset not found: {ref}")
        return self._row_to_dict(row)

    def _write_audit(
        self,
        db: sqlite3.Connection,
        *,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        details: dict[str, Any],
    ) -> None:
        db.execute(
            """
            INSERT INTO audit_log (actor, action, target_type, target_id, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (actor, action, target_type, target_id, json.dumps(details, sort_keys=True)),
        )

    def _fetch_all(self, query: str, parameters: tuple = ()) -> list[dict[str, Any]]:
        with self.connect() as db:
            return [self._row_to_dict(row) for row in db.execute(query, parameters)]

    @staticmethod
    def _get_row(db: sqlite3.Connection, query: str, parameters: tuple = ()) -> sqlite3.Row:
        row = db.execute(query, parameters).fetchone()
        if row is None:
            raise ValueError("record not found")
        return row

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | dict[str, Any]) -> dict[str, Any]:
        return dict(row)

    @staticmethod
    def _expand_asset_json(asset: dict[str, Any]) -> None:
        asset["ip_classification"] = json.loads(asset.pop("ip_classification_json") or "{}")
        asset["posture"] = json.loads(asset.pop("posture_json") or "{}")
        asset["risk_reasons"] = json.loads(asset.pop("risk_reasons_json") or "[]")
        asset["metadata"] = json.loads(asset.pop("metadata_json") or "{}")


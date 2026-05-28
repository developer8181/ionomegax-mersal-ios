# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Hash-chained audit log for regulatory and government compliance."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any


class AuditChain:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.db = connection

    def last_hash(self) -> str:
        row = self.db.execute(
            "SELECT record_hash FROM audit_log WHERE record_hash != '' ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
        if row and row[0]:
            return str(row[0])
        meta = self.db.execute(
            "SELECT meta_value FROM audit_chain_meta WHERE meta_key = 'genesis'"
        ).fetchone()
        return str(meta[0]) if meta else "MERSAL-AUDIT-GENESIS-v7"

    def seal_record(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        details: dict[str, Any],
        tenant_id: str,
    ) -> tuple[str, str]:
        prev = self.last_hash()
        payload = json.dumps(
            {
                "prev": prev,
                "actor": actor,
                "action": action,
                "target": target,
                "tenant_id": tenant_id,
                "details": details,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        record_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return prev, record_hash

    def verify_chain(self, *, limit: int = 500) -> dict[str, Any]:
        rows = self.db.execute(
            "SELECT audit_id, actor, action, target, details, tenant_id, prev_hash, record_hash "
            "FROM audit_log ORDER BY audit_id ASC LIMIT ?",
            (limit,),
        ).fetchall()
        expected_prev = self.db.execute(
            "SELECT meta_value FROM audit_chain_meta WHERE meta_key = 'genesis'"
        ).fetchone()
        chain_prev = str(expected_prev[0]) if expected_prev else "MERSAL-AUDIT-GENESIS-v7"
        broken_at: int | None = None
        checked = 0
        for row in rows:
            checked += 1
            if row["prev_hash"] and row["prev_hash"] != chain_prev:
                broken_at = int(row["audit_id"])
                break
            if row["record_hash"]:
                payload = json.dumps(
                    {
                        "prev": row["prev_hash"],
                        "actor": row["actor"],
                        "action": row["action"],
                        "target": row["target"],
                        "tenant_id": row["tenant_id"],
                        "details": json.loads(row["details"] or "{}"),
                    },
                    sort_keys=True,
                    ensure_ascii=False,
                )
                digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
                if digest != row["record_hash"]:
                    broken_at = int(row["audit_id"])
                    break
                chain_prev = row["record_hash"]
        return {
            "valid": broken_at is None,
            "records_checked": checked,
            "broken_at_audit_id": broken_at,
        }

# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""SQL dialect helpers — SQLite default, PostgreSQL when MERSAL_POSTGRES_DSN is set."""

from __future__ import annotations

import re
from typing import Any

from .adapter import uses_postgres

_INSERT_CONFLICT_KEY: dict[str, str] = {
    "policies": "policy_id",
    "endpoints": "endpoint_id",
    "threat_intel_cache": "indicator",
    "soar_playbooks": "playbook_id",
    "siem_rules": "rule_id",
    "incidents": "incident_id",
    "compliance_controls": "control_id",
    "yara_rules": "rule_id",
    "siem_window_rules": "rule_id",
    "tenants": "tenant_id",
    "platform_settings": "setting_key",
    "audit_chain_meta": "meta_key",
}


def adapt_sql(sql: str) -> str:
    if not uses_postgres():
        return sql
    out = sql.replace("?", "%s")
    match = re.search(r"INSERT\s+OR\s+IGNORE\s+INTO\s+(\w+)", out, flags=re.IGNORECASE)
    if match:
        table = match.group(1).lower()
        conflict_col = _INSERT_CONFLICT_KEY.get(table)
        if conflict_col:
            out = re.sub(
                r"INSERT\s+OR\s+IGNORE\s+INTO",
                "INSERT INTO",
                out,
                count=1,
                flags=re.IGNORECASE,
            )
            out = out.rstrip().rstrip(";") + f" ON CONFLICT ({conflict_col}) DO NOTHING"
    if re.search(r"last_insert_rowid\s*\(\s*\)", out, re.IGNORECASE):
        raise ValueError("last_insert_rowid() is not portable; use RETURNING event_id")
    return out


def events_window_count_sql(
    *,
    endpoint_id: str,
    window_seconds: int,
    event_type: str = "*",
    action_filter: str = "*",
) -> tuple[str, list[Any]]:
    params: list[Any] = [endpoint_id]
    if uses_postgres():
        query = """
            SELECT COUNT(*) FROM events
            WHERE endpoint_id = %s
            AND created_at::timestamptz >= NOW() - make_interval(secs => %s)
        """
        params.append(int(window_seconds))
    else:
        query = """
            SELECT COUNT(*) FROM events
            WHERE endpoint_id = ?
            AND datetime(created_at) >= datetime('now', ?)
        """
        params.append(f"-{int(window_seconds)} seconds")
    if event_type != "*":
        query += " AND event_type = ?" if not uses_postgres() else " AND event_type = %s"
        params.append(event_type)
    if action_filter != "*":
        query += " AND action = ?" if not uses_postgres() else " AND action = %s"
        params.append(action_filter)
    if uses_postgres():
        query = query.replace("?", "%s")
    return query, params

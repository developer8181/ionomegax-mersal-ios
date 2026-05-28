# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Schema migrations for Mersal Enterprise v7 — tenant scope + tamper-evident audit."""

from __future__ import annotations

import sqlite3


V7_STATEMENTS = """
CREATE TABLE IF NOT EXISTS audit_chain_meta (
    meta_key TEXT PRIMARY KEY,
    meta_value TEXT NOT NULL DEFAULT ''
);
"""


def apply_v7_migrations(connection: sqlite3.Connection) -> None:
    connection.executescript(V7_STATEMENTS)
    _add_column_if_missing(connection, "policies", "tenant_id", "TEXT NOT NULL DEFAULT 'default'")
    _add_column_if_missing(connection, "agents", "tenant_id", "TEXT NOT NULL DEFAULT 'default'")
    _add_column_if_missing(connection, "audit_log", "tenant_id", "TEXT NOT NULL DEFAULT 'default'")
    _add_column_if_missing(connection, "audit_log", "record_hash", "TEXT NOT NULL DEFAULT ''")
    _add_column_if_missing(connection, "audit_log", "prev_hash", "TEXT NOT NULL DEFAULT ''")
    connection.execute(
        """
        INSERT OR IGNORE INTO audit_chain_meta (meta_key, meta_value)
        VALUES ('genesis', 'MERSAL-AUDIT-GENESIS-v7')
        """
    )


def _add_column_if_missing(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    names = {row[1] for row in rows}
    if column not in names:
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

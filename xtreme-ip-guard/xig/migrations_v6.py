# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Schema migrations for Mersal Global Platform v6."""

from __future__ import annotations

import sqlite3


V6_STATEMENTS = """
CREATE TABLE IF NOT EXISTS tenants (
    tenant_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'enterprise',
    region TEXT NOT NULL DEFAULT 'global',
    metadata TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS rbac_users (
    user_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    username TEXT NOT NULL,
    password_hash TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'analyst',
    display_name TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, username)
);

CREATE TABLE IF NOT EXISTS webhooks (
    webhook_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    events TEXT NOT NULL DEFAULT '[]',
    secret TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS siem_window_rules (
    rule_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    window_seconds INTEGER NOT NULL DEFAULT 300,
    threshold INTEGER NOT NULL DEFAULT 5,
    event_type TEXT NOT NULL DEFAULT '*',
    action_filter TEXT NOT NULL DEFAULT '*',
    severity INTEGER NOT NULL DEFAULT 60,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS soc_sla_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    incident_id TEXT NOT NULL DEFAULT '',
    metric_type TEXT NOT NULL,
    target_minutes INTEGER NOT NULL,
    actual_minutes INTEGER,
    met INTEGER NOT NULL DEFAULT 0,
    computed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS platform_settings (
    setting_key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def apply_v6_migrations(connection: sqlite3.Connection) -> None:
    connection.executescript(V6_STATEMENTS)
    _add_column_if_missing(connection, "endpoints", "tenant_id", "TEXT NOT NULL DEFAULT 'default'")
    _add_column_if_missing(connection, "events", "tenant_id", "TEXT NOT NULL DEFAULT 'default'")
    _add_column_if_missing(connection, "incidents", "tenant_id", "TEXT NOT NULL DEFAULT 'default'")
    _add_column_if_missing(connection, "siem_alerts", "tenant_id", "TEXT NOT NULL DEFAULT 'default'")
    connection.execute(
        """
        INSERT OR IGNORE INTO tenants (tenant_id, name, slug, plan, region)
        VALUES ('default', 'Default Organization', 'default', 'enterprise', 'global')
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO platform_settings (setting_key, value)
        VALUES ('platform_version', '{"version":"6.0.0","tier":"global"}')
        """
    )


def _add_column_if_missing(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    if any(row[1] == column for row in rows):
        return
    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

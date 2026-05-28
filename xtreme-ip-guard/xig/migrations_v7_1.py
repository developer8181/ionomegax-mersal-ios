# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Mersal v7.1 — per-agent API keys and security events."""

from __future__ import annotations

import sqlite3


def apply_v7_1_migrations(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS agent_api_keys (
            agent_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            key_hash TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            rotated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS security_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            severity TEXT NOT NULL DEFAULT 'medium',
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            source_ip TEXT NOT NULL DEFAULT '',
            details TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

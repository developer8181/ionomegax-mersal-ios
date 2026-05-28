# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Mersal v8 — standalone platform: SIEM forwarders, OIDC, backups metadata."""

from __future__ import annotations

import sqlite3


def apply_v8_migrations(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS siem_forwarders (
            forwarder_id TEXT PRIMARY KEY,
            tenant_id TEXT NOT NULL DEFAULT 'default',
            name TEXT NOT NULL,
            protocol TEXT NOT NULL DEFAULT 'syslog_udp',
            host TEXT NOT NULL,
            port INTEGER NOT NULL DEFAULT 514,
            format TEXT NOT NULL DEFAULT 'cef',
            enabled INTEGER NOT NULL DEFAULT 1,
            filters TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS oidc_clients (
            client_key TEXT PRIMARY KEY,
            issuer_url TEXT NOT NULL,
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL DEFAULT '',
            redirect_uri TEXT NOT NULL,
            scopes TEXT NOT NULL DEFAULT 'openid profile email',
            default_role TEXT NOT NULL DEFAULT 'analyst',
            tenant_id TEXT NOT NULL DEFAULT 'default',
            enabled INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS platform_backups (
            backup_id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            size_bytes INTEGER NOT NULL DEFAULT 0,
            checksum TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS platform_heartbeats (
            component TEXT PRIMARY KEY,
            status TEXT NOT NULL DEFAULT 'ok',
            detail TEXT NOT NULL DEFAULT '{}',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

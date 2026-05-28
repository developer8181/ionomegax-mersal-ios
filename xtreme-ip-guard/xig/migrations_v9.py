# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Mersal v9 — SAML, SCIM, signed update channel."""

from __future__ import annotations

import sqlite3


V9_STATEMENTS = """
CREATE TABLE IF NOT EXISTS saml_providers (
    provider_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    sso_url TEXT NOT NULL,
    x509_cert TEXT NOT NULL DEFAULT '',
    default_role TEXT NOT NULL DEFAULT 'analyst',
    tenant_id TEXT NOT NULL DEFAULT 'default',
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS scim_tokens (
    token_id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL DEFAULT 'default',
    token_hash TEXT NOT NULL,
    label TEXT NOT NULL DEFAULT 'scim',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS update_manifests (
    manifest_id TEXT PRIMARY KEY,
    component TEXT NOT NULL,
    version TEXT NOT NULL,
    artifact_url TEXT NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    signature TEXT NOT NULL,
    published_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def apply_v9_migrations(connection: sqlite3.Connection) -> None:
    connection.executescript(V9_STATEMENTS)

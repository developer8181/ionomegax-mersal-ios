# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""PostgreSQL health — connectivity, version, optional replica lag."""

from __future__ import annotations

import os
from typing import Any

from ..config import postgres_dsn
from ..db.adapter import uses_postgres


def postgres_cluster_health() -> dict[str, Any]:
    if not uses_postgres():
        return {"active": False, "ok": False, "detail": "SQLite backend (set MERSAL_POSTGRES_DSN for HA)"}
    dsn = postgres_dsn()
    primary = _probe(dsn)
    replica_dsn = os.environ.get("MERSAL_PG_REPLICA_DSN", "").strip()
    result: dict[str, Any] = {
        "active": True,
        "ok": primary.get("ok", False),
        "primary": primary,
        "replica_configured": bool(replica_dsn),
    }
    if replica_dsn:
        replica = _probe(replica_dsn)
        result["replica"] = replica
        lag = _replication_lag_seconds(dsn)
        result["replication_lag_seconds"] = lag
        result["ok"] = primary.get("ok") and replica.get("ok") and (lag is None or lag < 30)
    return result


def _probe(dsn: str) -> dict[str, Any]:
    try:
        import psycopg
    except ImportError:
        return {"ok": False, "error": "psycopg not installed"}
    try:
        with psycopg.connect(dsn, connect_timeout=8) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = str(cur.fetchone()[0])
                cur.execute("SELECT 1")
        return {"ok": True, "version": version.split(",")[0]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def _replication_lag_seconds(primary_dsn: str) -> float | None:
    try:
        import psycopg
    except ImportError:
        return None
    try:
        with psycopg.connect(primary_dsn, connect_timeout=8) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(
                        EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())),
                        0
                    )
                    FROM pg_stat_replication
                    LIMIT 1
                    """
                )
                row = cur.fetchone()
                if not row or row[0] is None:
                    return None
                return float(row[0])
    except Exception:  # noqa: BLE001
        return None

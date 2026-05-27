"""Health and readiness helpers."""

from __future__ import annotations

from typing import Any

from .storage import Database


def health_report(database: Database, *, settings_summary: dict[str, Any]) -> dict[str, Any]:
    try:
        with database.connect() as db:
            db.execute("SELECT 1").fetchone()
        database_ok = True
    except OSError:
        database_ok = False
    dashboard = database.dashboard() if database_ok else {}
    return {
        "status": "healthy" if database_ok else "degraded",
        "database": database_ok,
        "settings": settings_summary,
        "agents": dashboard.get("agents", 0) if database_ok else 0,
        "jobs": dashboard.get("jobs", 0) if database_ok else 0,
    }

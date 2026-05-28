# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Mersal Log Vault — centralized log ingestion and search (SIEM data lake)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class LogVault:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def ingest_batch(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        stored = 0
        for item in records[:500]:
            self.db.ingest_log_record(
                source=str(item.get("source", "agent")),
                message=str(item.get("message", "")),
                host=str(item.get("host", "")),
                facility=str(item.get("facility", "")),
                severity=int(item.get("severity", 30)),
                endpoint_id=str(item.get("endpoint_id", "")),
                raw=str(item.get("raw", "")),
                metadata=dict(item.get("metadata", {})),
            )
            stored += 1
        return {"ingested": stored}

    def search(self, *, query: str = "", limit: int = 100) -> list[dict[str, Any]]:
        return self.db.search_logs(query=query, limit=limit)

    def dashboard(self) -> dict[str, Any]:
        return {
            "module": "Mersal Log Vault",
            "summary": self.db.logvault_summary(),
            "recent": self.db.search_logs(limit=20),
        }

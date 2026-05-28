# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""TAXII 2.0 client — poll STIX indicators from enterprise feeds."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class TaxiiClient:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def sync(self, *, discovery_url: str = "", collection_id: str = "") -> dict[str, Any]:
        url = (discovery_url or os.environ.get("MERSAL_TAXII_URL", "")).strip()
        collection = (collection_id or os.environ.get("MERSAL_TAXII_COLLECTION", "default")).strip()
        if not url:
            return {"synced": 0, "skipped": True, "reason": "MERSAL_TAXII_URL not set"}
        objects_url = url.rstrip("/")
        if not objects_url.endswith("/objects"):
            objects_url = f"{objects_url}/collections/{collection}/objects/"
        added = 0
        try:
            req = urllib.request.Request(objects_url, headers={"Accept": "application/taxii+json;version=2.1"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            return {"synced": 0, "error": str(exc)}
        for obj in payload.get("objects", []):
            if obj.get("type") != "indicator":
                continue
            pattern = str(obj.get("pattern", ""))
            indicator = self._extract_indicator(pattern)
            if not indicator:
                continue
            self.db.upsert_threat_indicator(
                indicator=indicator,
                ioc_type="domain" if "." in indicator else "hash",
                severity=70,
                source="taxii",
                metadata={"stix_id": obj.get("id"), "name": obj.get("name", "")},
            )
            added += 1
        self.db.record_threat_feed_sync("taxii", added, {"url": objects_url})
        return {"synced": added, "url": objects_url}

    @staticmethod
    def _extract_indicator(pattern: str) -> str:
        for token in ("domain-name:value=", "url:value=", "file:hashes.'SHA-256'="):
            if token in pattern:
                part = pattern.split(token, 1)[1]
                return part.strip(" '\"[]")
        return ""

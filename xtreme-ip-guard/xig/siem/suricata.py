# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Suricata IDS eve.json ingestion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .mitre import map_suricata_category

if TYPE_CHECKING:
    from ..storage import Database


def parse_eve_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    if payload.get("event_type") != "alert":
        return None
    alert = payload.get("alert") or {}
    return {
        "signature_id": int(alert.get("signature_id", 0)),
        "signature": str(alert.get("signature", "Suricata alert")),
        "category": str(alert.get("category", "")),
        "severity": int(alert.get("severity", 2)) * 25,
        "src_ip": str((payload.get("src_ip") or "")),
        "dest_ip": str((payload.get("dest_ip") or "")),
        "proto": str(payload.get("proto", "")),
        "mitre_technique": map_suricata_category(str(alert.get("category", ""))),
        "payload": payload,
    }


def ingest_eve_file(database: "Database", path: str | Path, *, limit: int = 200) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        return {"ingested": 0, "error": "file_not_found"}
    ingested = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if ingested >= limit:
                break
            parsed = parse_eve_line(line)
            if parsed:
                database.record_suricata_alert(parsed)
                ingested += 1
    return {"ingested": ingested, "path": str(path)}


class SuricataIngester:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def ingest_payload(self, alerts: list[dict[str, Any]]) -> dict[str, Any]:
        count = 0
        for item in alerts[:100]:
            if "signature" in item:
                item.setdefault("mitre_technique", map_suricata_category(str(item.get("category", ""))))
                self.db.record_suricata_alert(item)
                count += 1
        return {"ingested": count}

    def dashboard(self) -> dict[str, Any]:
        return {
            "module": "Mersal IDS (Suricata)",
            "open_alerts": len(self.db.list_suricata_alerts()),
            "recent": self.db.list_suricata_alerts(limit=15),
        }

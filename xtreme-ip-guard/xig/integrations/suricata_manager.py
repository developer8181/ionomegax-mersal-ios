# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Suricata IDS integration — ingest EVE when Suricata is installed on the host."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..fabric import MersalSecurityFabric
    from ..storage import Database


class SuricataManager:
    def __init__(self, database: "Database", fabric: "MersalSecurityFabric") -> None:
        self.db = database
        self.fabric = fabric

    def status(self) -> dict[str, Any]:
        binary = shutil.which("suricata")
        eve = os.environ.get("MERSAL_SURICATA_EVE", "/var/log/suricata/eve.json")
        return {
            "installed": bool(binary),
            "binary": binary or "",
            "eve_path": eve,
            "eve_exists": Path(eve).is_file(),
        }

    def sync_if_available(self) -> dict[str, Any]:
        st = self.status()
        if not st["eve_exists"]:
            return {**st, "ingested": 0, "skipped": True}
        ingested = 0
        path = Path(st["eve_path"])
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-500:]
            alerts = []
            for line in lines:
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if obj.get("event_type") == "alert":
                    alerts.append(obj)
            if alerts:
                result = self.fabric.enterprise.suricata.ingest_payload(alerts)
                ingested = int(result.get("ingested", len(alerts)))
        except OSError as exc:
            return {**st, "error": str(exc), "ingested": 0}
        return {**st, "ingested": ingested}

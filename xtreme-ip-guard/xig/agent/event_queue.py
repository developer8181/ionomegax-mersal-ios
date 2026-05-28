# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Disk-backed event queue — agents survive network outages (enterprise endpoints)."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any


class AgentEventQueue:
    def __init__(self, state_dir: Path, *, max_items: int = 500) -> None:
        self.queue_dir = state_dir / "queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.max_items = max_items

    def enqueue(self, payload: dict[str, Any]) -> str:
        self._prune_if_needed()
        item_id = secrets.token_hex(8)
        path = self.queue_dir / f"{item_id}.json"
        path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        return item_id

    def pending(self) -> list[tuple[str, dict[str, Any]]]:
        items: list[tuple[str, dict[str, Any]]] = []
        for path in sorted(self.queue_dir.glob("*.json")):
            try:
                items.append((path.stem, json.loads(path.read_text(encoding="utf-8"))))
            except (json.JSONDecodeError, OSError):
                path.unlink(missing_ok=True)
        return items

    def ack(self, item_id: str) -> None:
        path = self.queue_dir / f"{item_id}.json"
        path.unlink(missing_ok=True)

    def depth(self) -> int:
        return len(list(self.queue_dir.glob("*.json")))

    def _prune_if_needed(self) -> None:
        paths = sorted(self.queue_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        while len(paths) >= self.max_items:
            paths.pop(0).unlink(missing_ok=True)

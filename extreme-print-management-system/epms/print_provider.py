"""Print-provider primitives for spooler and gateway integrations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SpoolEvent:
    user_id: int
    printer_id: int
    document_name: str
    pages: int
    copies: int = 1
    color: bool = False
    duplex: bool = False
    account: str = "Personal"
    source: str = "print-provider"
    agent_id: str = ""
    spool_id: str = ""

    def to_job_payload(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.pages <= 0:
            raise ValueError("pages must be greater than zero")
        if self.copies <= 0:
            raise ValueError("copies must be greater than zero")
        payload["document_name"] = self.document_name.strip() or "Untitled document"
        payload["account"] = self.account.strip() or "Personal"
        return payload


class OfflineQueue:
    """Append-only local queue for events captured while the server is offline."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def enqueue(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        events: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid queue entry at line {line_number}") from exc
        return events

    def replace(self, events: list[dict[str, Any]]) -> None:
        if not events:
            self.clear()
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
        tmp_path.replace(self.path)

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def count(self) -> int:
        return len(self.read_all())


def parse_spool_event(data: dict[str, Any], *, default_source: str = "print-provider", default_agent_id: str = "") -> SpoolEvent:
    return SpoolEvent(
        user_id=int(data["user_id"]),
        printer_id=int(data["printer_id"]),
        document_name=str(data.get("document_name", "")),
        pages=int(data["pages"]),
        copies=int(data.get("copies", 1)),
        color=bool(data.get("color", False)),
        duplex=bool(data.get("duplex", False)),
        account=str(data.get("account", "Personal")),
        source=str(data.get("source", default_source)),
        agent_id=str(data.get("agent_id", default_agent_id)),
        spool_id=str(data.get("spool_id", "")),
    )

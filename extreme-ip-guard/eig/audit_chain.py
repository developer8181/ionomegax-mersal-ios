"""Tamper-evident audit log chain (hash-linked entries, prototype)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


GENESIS_HASH = "0" * 64


@dataclass(frozen=True)
class AuditEntry:
    sequence: int
    event_type: str
    payload: dict[str, Any]
    previous_hash: str
    entry_hash: str
    created_at: str


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def compute_entry_hash(
    *,
    sequence: int,
    event_type: str,
    payload: dict[str, Any],
    previous_hash: str,
    created_at: str,
) -> str:
    material = "|".join(
        [
            str(sequence),
            event_type,
            _canonical(payload),
            previous_hash,
            created_at,
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def append_entry(
    *,
    sequence: int,
    event_type: str,
    payload: dict[str, Any],
    previous_hash: str,
    created_at: str,
) -> AuditEntry:
    entry_hash = compute_entry_hash(
        sequence=sequence,
        event_type=event_type,
        payload=payload,
        previous_hash=previous_hash,
        created_at=created_at,
    )
    return AuditEntry(
        sequence=sequence,
        event_type=event_type,
        payload=payload,
        previous_hash=previous_hash,
        entry_hash=entry_hash,
        created_at=created_at,
    )


def verify_chain(entries: list[AuditEntry]) -> dict[str, Any]:
    """Verify integrity of a sequence of audit entries."""
    if not entries:
        return {"valid": True, "checked": 0, "broken_at": None}

    expected_prev = GENESIS_HASH
    for entry in sorted(entries, key=lambda item: item.sequence):
        if entry.previous_hash != expected_prev:
            return {"valid": False, "checked": entry.sequence, "broken_at": entry.sequence}
        recomputed = compute_entry_hash(
            sequence=entry.sequence,
            event_type=entry.event_type,
            payload=entry.payload,
            previous_hash=entry.previous_hash,
            created_at=entry.created_at,
        )
        if recomputed != entry.entry_hash:
            return {"valid": False, "checked": entry.sequence, "broken_at": entry.sequence}
        expected_prev = entry.entry_hash
    return {"valid": True, "checked": len(entries), "broken_at": None}

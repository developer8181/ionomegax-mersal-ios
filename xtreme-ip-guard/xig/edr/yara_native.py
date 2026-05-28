# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Optional libYARA scanning — falls back to regex engine when unavailable."""

from __future__ import annotations

from typing import Any

_YARA: Any = None
try:
    import yara  # type: ignore[import-untyped]

    _YARA = yara
except ImportError:
    _YARA = None


def yara_available() -> bool:
    return _YARA is not None


def compile_rules(rule_sources: dict[str, str]) -> Any | None:
    if not _YARA:
        return None
    return _YARA.compile(sources=rule_sources)


def scan_process_blob(blob: str, compiled: Any) -> list[dict[str, Any]]:
    if not compiled:
        return []
    matches = compiled.match(data=blob.encode("utf-8", errors="replace"))
    return [
        {
            "rule_id": f"YARA-{m.rule}",
            "name": m.rule,
            "meta": dict(m.meta) if m.meta else {},
            "tags": list(m.tags),
            "engine": "libyara",
        }
        for m in matches
    ]

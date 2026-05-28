# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""EDR file integrity monitoring for critical system paths."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

CRITICAL_PATHS = (
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "/etc/ssh/sshd_config",
)


def scan_critical_files(state_dir: Path) -> list[dict[str, Any]]:
    state_file = state_dir / "fim-baseline.json"
    baseline = _load_baseline(state_file)
    findings: list[dict[str, Any]] = []
    current: dict[str, str] = {}

    for path_str in CRITICAL_PATHS:
        path = Path(path_str)
        if not path.is_file():
            continue
        digest = _hash_file(path)
        current[path_str] = digest
        previous = baseline.get(path_str)
        if previous and previous != digest:
            findings.append(
                {
                    "path": path_str,
                    "change": "modified",
                    "severity": 85,
                    "title": f"Critical file modified: {path_str}",
                }
            )
        elif not previous:
            findings.append(
                {
                    "path": path_str,
                    "change": "baseline",
                    "severity": 10,
                    "title": f"FIM baseline recorded: {path_str}",
                }
            )

    _save_baseline(state_file, current)
    return findings


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes()[:65536])
    return digest.hexdigest()


def _load_baseline(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    import json

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_baseline(path: Path, data: dict[str, str]) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, sort_keys=True, indent=2), encoding="utf-8")

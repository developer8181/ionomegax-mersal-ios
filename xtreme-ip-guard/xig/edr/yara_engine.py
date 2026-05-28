# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""YARA-style pattern engine for processes and command lines."""

from __future__ import annotations

import re
from typing import Any

DEFAULT_YARA_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "YARA-MIMIKATZ",
        "name": "Credential dumping tool",
        "pattern": r"mimikatz|sekurlsa|lsadump",
        "target": "process",
        "severity": 95,
        "mitre_technique": "T1003",
    },
    {
        "rule_id": "YARA-POWERSHELL-ENC",
        "name": "Encoded PowerShell",
        "pattern": r"powershell.*(-enc|-encodedcommand)",
        "target": "process",
        "severity": 85,
        "mitre_technique": "T1059.001",
    },
    {
        "rule_id": "YARA-RANSOM-EXT",
        "name": "Ransomware extension pattern",
        "pattern": r"\.(locked|encrypted|crypt|ryuk)",
        "target": "path",
        "severity": 90,
        "mitre_technique": "T1486",
    },
    {
        "rule_id": "YARA-REVERSE-SHELL",
        "name": "Reverse shell binary",
        "pattern": r"nc\.exe|ncat|/dev/tcp/|bash\s+-i",
        "target": "process",
        "severity": 88,
        "mitre_technique": "T1059.004",
    },
    {
        "rule_id": "YARA-CERTUTIL",
        "name": "LOLBIN certutil download",
        "pattern": r"certutil.*(-urlcache|-decode)",
        "target": "process",
        "severity": 80,
        "mitre_technique": "T1105",
    },
]


def scan_text(blob: str, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    text = blob.lower()
    for rule in rules:
        if not rule.get("enabled", True):
            continue
        try:
            if re.search(str(rule["pattern"]), text, re.IGNORECASE):
                matches.append(rule)
        except re.error:
            continue
    return matches


def scan_processes(processes: list[dict[str, Any]], rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for proc in processes:
        blob = f"{proc.get('comm', '')} {proc.get('args', '')}"
        for rule in scan_text(blob, [r for r in rules if r.get("target") == "process"]):
            hits.append({**rule, "process": proc})
    return hits

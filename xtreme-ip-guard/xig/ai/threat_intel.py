# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Threat intelligence matching (defensive IOC cache)."""

from __future__ import annotations

from typing import Any


DEFAULT_IOCS: list[dict[str, Any]] = [
    {"indicator": "pastebin.com", "ioc_type": "domain", "severity": 70, "source": "mersal-feed"},
    {"indicator": "anonfiles", "ioc_type": "domain", "severity": 75, "source": "mersal-feed"},
    {"indicator": "mega.nz", "ioc_type": "domain", "severity": 60, "source": "mersal-feed"},
    {"indicator": "tor2web", "ioc_type": "domain", "severity": 85, "source": "mersal-feed"},
    {"indicator": "credential", "ioc_type": "classification", "severity": 90, "source": "mersal-feed"},
]


def match_destination(destination: str, indicators: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lowered = destination.lower()
    hits: list[dict[str, Any]] = []
    for item in indicators:
        needle = str(item.get("indicator", "")).lower()
        if needle and needle in lowered:
            hits.append(item)
    return hits

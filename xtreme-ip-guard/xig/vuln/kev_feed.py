# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""CISA Known Exploited Vulnerabilities — real government feed integration."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def fetch_kev_indicators(url: str, *, timeout: int = 30) -> list[dict[str, Any]]:
    """Download and normalize CISA KEV catalog into threat-intel indicators."""
    if not url:
        return []
    request = urllib.request.Request(url, headers={"User-Agent": "Mersal-Guard/3.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError):
        return []

    vulnerabilities = payload.get("vulnerabilities") or []
    indicators: list[dict[str, Any]] = []
    for item in vulnerabilities[:500]:
        if not isinstance(item, dict):
            continue
        cve = str(item.get("cveID", ""))
        if not cve:
            continue
        indicators.append(
            {
                "indicator": cve.lower(),
                "ioc_type": "cve",
                "severity": 95,
                "source": "cisa-kev",
                "vendor": item.get("vendorProject", ""),
                "product": item.get("product", ""),
                "title": item.get("vulnerabilityName", cve),
            }
        )
    return indicators

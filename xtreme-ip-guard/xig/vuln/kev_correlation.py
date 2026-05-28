# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Correlate vulnerability findings with CISA KEV indicators in threat intel cache."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..storage import Database


def load_kev_cves(database: "Database") -> set[str]:
    found: set[str] = set()
    for row in database.list_threat_intel():
        if row.get("source") != "cisa-kev":
            continue
        if str(row.get("ioc_type", "")).lower() != "cve":
            continue
        indicator = str(row.get("indicator", "")).strip().upper()
        if indicator.startswith("CVE-"):
            found.add(indicator)
    return found


def apply_kev_priority(
    *,
    cve_id: str,
    title: str,
    severity: float,
    kev_cves: set[str],
) -> tuple[str, float, bool]:
    normalized = cve_id.strip().upper()
    if normalized not in kev_cves:
        return title, severity, False
    kev_title = title if "[CISA KEV]" in title else f"{title} [CISA KEV]"
    return kev_title, max(severity, 9.5), True

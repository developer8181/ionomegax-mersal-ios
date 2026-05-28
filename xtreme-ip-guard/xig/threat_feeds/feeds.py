# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Global threat feeds — bundled STIX + optional remote sync."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import TYPE_CHECKING, Any

from ..ai.threat_intel import DEFAULT_IOCS
from ..vuln.kev_feed import fetch_kev_indicators
from .stix import parse_stix_bundle

if TYPE_CHECKING:
    from ..storage import Database

# Bundled Mersal Global Threat Feed (STIX-style bundle, offline-first).
MERSAL_GLOBAL_STIX: dict[str, Any] = {
    "type": "bundle",
    "id": "bundle--mersal-global-2026",
    "objects": [
        {
            "type": "indicator",
            "id": "indicator--mersal-ransom",
            "pattern": "[domain-name:value='lockbit leak site.onion']",
            "labels": ["malicious-activity"],
        },
        {
            "type": "indicator",
            "id": "indicator--mersal-exfil",
            "pattern": "[domain-name:value='doubleextortion.pro']",
            "labels": ["malware"],
        },
        {
            "type": "indicator",
            "id": "indicator--mersal-c2",
            "pattern": "[ipv4-addr:value='185.220.101.0']",
            "labels": ["malicious-activity"],
        },
        {
            "type": "indicator",
            "id": "indicator--mersal-phish",
            "pattern": "[url:value='http://microsoft-login-verify.tk']",
            "labels": ["phishing"],
        },
    ],
}


class ThreatFeedSync:
    def __init__(self, database: "Database") -> None:
        self.db = database

    def sync_all(self, *, remote_url: str = "", kev_url: str = "") -> dict[str, Any]:
        added = 0
        feeds = ["mersal-builtin", "mersal-global-stix"]
        added += self.db.seed_threat_intel(DEFAULT_IOCS)
        stix_indicators = parse_stix_bundle(MERSAL_GLOBAL_STIX, source="mersal-global-stix")
        added += self.db.seed_threat_intel(stix_indicators)

        kev = kev_url or _default_kev_url()
        if kev:
            kev_indicators = fetch_kev_indicators(kev)
            if kev_indicators:
                added += self.db.seed_threat_intel(kev_indicators)
                feeds.append("cisa-kev")
                self.db.record_threat_feed_sync("cisa-kev", len(kev_indicators))

        if remote_url:
            try:
                request = urllib.request.Request(remote_url, headers={"User-Agent": "Mersal-Guard/2.0"})
                with urllib.request.urlopen(request, timeout=15) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                remote = parse_stix_bundle(payload, source="remote-stix")
                added += self.db.seed_threat_intel(remote)
            except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
                self.db.record_threat_feed_sync("remote", 0, error=str(exc))
                return self._result(added, remote_error=str(exc))

        total = len(self.db.list_threat_intel())
        self.db.record_threat_feed_sync("mersal-global", added)
        return self._result(added, feeds=feeds, total_indicators=total)

    @staticmethod
    def _result(added: int, *, feeds: list[str] | None = None, **extra: Any) -> dict[str, Any]:
        return {"indicators_added": added, "feeds": feeds or ["mersal-builtin", "mersal-global-stix"], **extra}


def _default_kev_url() -> str:
    import os

    return os.environ.get(
        "MERSAL_KEV_FEED_URL",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    ).strip()

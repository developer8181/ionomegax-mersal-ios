"""STIX 2.x bundle parser (indicators → Mersal IOC records)."""

from __future__ import annotations

from typing import Any


def parse_stix_bundle(bundle: dict[str, Any], *, source: str = "stix-feed") -> list[dict[str, Any]]:
    """Extract domain/url/file-hash indicators from a STIX 2.0/2.1 bundle."""
    objects = bundle.get("objects") or []
    indicators: list[dict[str, Any]] = []

    for obj in objects:
        if not isinstance(obj, dict):
            continue
        if obj.get("type") != "indicator":
            continue
        pattern = str(obj.get("pattern", ""))
        severity = 70
        labels = obj.get("labels") or []
        if "malicious-activity" in labels or "malware" in labels:
            severity = 85

        for needle, ioc_type in _extract_pattern_values(pattern):
            indicators.append(
                {
                    "indicator": needle,
                    "ioc_type": ioc_type,
                    "severity": severity,
                    "source": source,
                    "stix_id": obj.get("id", ""),
                }
            )
    return indicators


def _extract_pattern_values(pattern: str) -> list[tuple[str, str]]:
    lowered = pattern.lower()
    found: list[tuple[str, str]] = []
    for marker, ioc_type in (
        ("domain-name:value=", "domain"),
        ("url:value=", "url"),
        ("file:hashes.md5", "hash"),
        ("file:hashes.sha256", "hash"),
        ("ipv4-addr:value=", "ip"),
    ):
        if marker in lowered:
            fragment = pattern.split("'", 2)
            if len(fragment) >= 2:
                value = fragment[1].strip()
                if value:
                    found.append((value, ioc_type))
    return found

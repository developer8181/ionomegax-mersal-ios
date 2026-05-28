"""Enterprise security posture score (0–100)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


def compute_posture(database: "Database") -> dict[str, Any]:
    endpoints = database.list_endpoints()
    findings = database.list_vuln_findings(limit=500, status="open")
    events = database.list_events()
    isolated = sum(1 for ep in endpoints if ep.get("isolated"))
    open_critical = sum(1 for f in findings if float(f.get("severity", 0)) >= 9.0)
    open_high = sum(1 for f in findings if 7.0 <= float(f.get("severity", 0)) < 9.0)
    blocked = sum(1 for e in events if e.get("action") in {"block", "quarantine", "isolate_endpoint"})
    ioc_count = len(database.list_threat_intel())
    baselines = database.count_baselines()

    penalty = min(60, open_critical * 15 + open_high * 5 + isolated * 2)
    bonus = min(25, baselines // 2 + ioc_count // 5 + (10 if blocked else 0))
    score = max(0, min(100, 88 - penalty + bonus))

    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 55:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    breakdown = {
        "endpoints": len(endpoints),
        "isolated_endpoints": isolated,
        "open_findings": len(findings),
        "critical_findings": open_critical,
        "high_findings": open_high,
        "threat_indicators": ioc_count,
        "ai_baselines": baselines,
        "defensive_events": len(events),
    }
    return database.save_security_posture(score=score, grade=grade, breakdown=breakdown)

# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Mersal Global Security Fabric — orchestration layer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..ai import MersalAICortex
from ..soar import SoarEngine
from ..threat_feeds import ThreatFeedSync
from ..vuln import VulnerabilityScanner
from .posture import compute_posture
from .scheduler import SecurityScheduler

if TYPE_CHECKING:
    from ..enterprise import MersalEnterpriseSuite
    from ..storage import Database


class MersalSecurityFabric:
    """Unified defensive stack: AI + vuln + threat intel + SOAR + posture."""

    def __init__(self, database: "Database") -> None:
        self.db = database
        self.cortex = MersalAICortex(database)
        self.scanner = VulnerabilityScanner(database)
        self.feeds = ThreatFeedSync(database)
        self.soar = SoarEngine(database)
        self.scheduler = SecurityScheduler(database, soar=self.soar, fabric=self)
        from ..enterprise import MersalEnterpriseSuite

        self.enterprise = MersalEnterpriseSuite(database, fabric=self)

    def dashboard(self) -> dict[str, Any]:
        posture = self.db.latest_security_posture()
        return {
            "fabric": "Mersal Global Security Fabric",
            "version": "4.0",
            "modules": [
                "neural_cortex",
                "vulnerability_management",
                "threat_intelligence",
                "soar",
                "siem",
                "edr",
                "incident_response",
                "compliance",
                "network_security",
                "daily_scheduler",
            ],
            "posture": posture,
            "ai": self.cortex.dashboard(),
            "vulnerabilities": self.db.vuln_summary(),
            "threat_intel": {"indicators": len(self.db.list_threat_intel())},
            "soar": self.db.soar_summary(),
            "scheduler": self.db.scheduler_summary(),
        }

    def run_daily_now(self) -> dict[str, Any]:
        return self.scheduler.run_daily_cycle()


__all__ = ["MersalSecurityFabric", "SecurityScheduler", "compute_posture"]

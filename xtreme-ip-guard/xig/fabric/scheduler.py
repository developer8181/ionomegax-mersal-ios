# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
"""Background scheduler — daily vulnerability scan, threat feeds, AI training."""

from __future__ import annotations

import os
import threading
import time
from typing import TYPE_CHECKING, Any

from ..threat_feeds import ThreatFeedSync
from ..vuln import VulnerabilityScanner
from .posture import compute_posture

if TYPE_CHECKING:
    from ..fabric import MersalSecurityFabric
    from ..soar import SoarEngine
    from ..storage import Database


class SecurityScheduler:
    def __init__(
        self,
        database: "Database",
        *,
        soar: "SoarEngine | None" = None,
        fabric: "MersalSecurityFabric | None" = None,
    ) -> None:
        self.db = database
        self.soar = soar
        self.fabric = fabric
        self.interval = int(os.environ.get("MERSAL_DAILY_INTERVAL_SECONDS", "86400"))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._loop, name="mersal-scheduler", daemon=True)
        self._thread.start()
        # Initial run shortly after boot
        threading.Thread(target=self._delayed_bootstrap, daemon=True).start()

    def stop(self) -> None:
        self._stop.set()

    def run_job(self, job_name: str) -> dict[str, Any]:
        if job_name == "threat_feeds":
            return self._run_threat_feeds()
        if job_name == "vuln_scan":
            return self._run_vuln_scan()
        if job_name == "ai_train":
            return self.db.train_cortex_from_history(limit=200)
        if job_name == "posture":
            return compute_posture(self.db)
        if job_name == "daily_all":
            return self.run_daily_cycle()
        if job_name == "enterprise_cycle":
            from ..enterprise import MersalEnterpriseSuite

            return MersalEnterpriseSuite(self.db, fabric=self.fabric).run_enterprise_cycle()
        if job_name == "siem_forward" and self.fabric:
            from ..integrations.siem_forwarder import SiemForwarder

            return SiemForwarder(self.db).forward_batch()
        if job_name == "autonomous_cycle" and self.fabric:
            from ..platform_ops.standalone import StandaloneController

            return StandaloneController(self.db, self.fabric).run_autonomous_cycle()
        if job_name == "backup":
            from ..platform_ops.backup import BackupManager

            return BackupManager(self.db).create_backup()
        raise ValueError(f"unknown job: {job_name}")

    def run_daily_cycle(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        jobs = ["threat_feeds", "vuln_scan", "ai_train", "posture", "backup"]
        if self.fabric and os.environ.get("MERSAL_AUTONOMOUS", "1").strip().lower() not in {"0", "false"}:
            jobs.extend(["siem_forward", "autonomous_cycle"])
        for job in jobs:
            try:
                results[job] = self.run_job(job)
                self.db.record_scheduler_run(job, "ok", results[job])
            except Exception as exc:  # noqa: BLE001
                results[job] = {"error": str(exc)}
                self.db.record_scheduler_run(job, "error", results[job])
        return results

    def _run_threat_feeds(self) -> dict[str, Any]:
        stix_url = os.environ.get("MERSAL_STIX_FEED_URL", "").strip()
        kev_url = os.environ.get(
            "MERSAL_KEV_FEED_URL",
            "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        ).strip()
        return ThreatFeedSync(self.db).sync_all(remote_url=stix_url, kev_url=kev_url)

    def _run_vuln_scan(self) -> dict[str, Any]:
        scanner = VulnerabilityScanner(self.db)
        result = scanner.scan_all_endpoints(scope="daily")
        if self.soar:
            for finding in self.db.list_vuln_findings(limit=20, status="open"):
                if float(finding.get("severity", 0)) >= 9.0:
                    self.soar.on_vuln_finding(finding)
        return result

    def _delayed_bootstrap(self) -> None:
        time.sleep(8)
        if not self._stop.is_set():
            self.run_daily_cycle()

    def _loop(self) -> None:
        while not self._stop.wait(self.interval):
            self.run_daily_cycle()

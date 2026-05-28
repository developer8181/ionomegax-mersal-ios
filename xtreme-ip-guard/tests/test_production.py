# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xig.bootstrap import bootstrap_organization, ENTERPRISE_POLICIES
from xig.config import allow_demo_seed, is_production
from xig.edr.process_intel import collect_running_processes, suspicious_process_events
from xig.readiness import production_readiness
from xig.storage import Database
from xig.vuln.nmap_probe import nmap_available, scan_host_ports


class ProductionTests(unittest.TestCase):
    def test_production_flag(self):
        with patch.dict(os.environ, {"MERSAL_PRODUCTION": "1"}, clear=False):
            self.assertTrue(is_production())
            self.assertFalse(allow_demo_seed())

    def test_demo_ui_allows_seed_in_production(self):
        env = {"MERSAL_PRODUCTION": "1", "MERSAL_DEMO_UI": "1"}
        with patch.dict(os.environ, env, clear=False):
            self.assertTrue(allow_demo_seed())

    def test_bootstrap_installs_policies(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "prod.sqlite3")
            db.init_schema()
            with patch("xig.bootstrap.MersalSecurityFabric") as mock_fabric:
                instance = mock_fabric.return_value
                instance.feeds.sync_all.return_value = {"indicators_added": 10}
                instance.scanner.scan_all_endpoints.return_value = {"findings_count": 2}
                instance.run_daily_now.return_value = {"threat_feeds": {}}
                summary = bootstrap_organization(db)
            self.assertEqual(summary["policies_installed"], len(ENTERPRISE_POLICIES))
            self.assertGreaterEqual(len(db.list_policies()), len(ENTERPRISE_POLICIES))

    def test_readiness_report_structure(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "ready.sqlite3")
            db.init_schema()
            db.seed_demo()
            with patch.dict(os.environ, {"MERSAL_PRODUCTION": "1", "MERSAL_API_TOKEN": "test-token"}, clear=False):
                report = production_readiness(db)
            self.assertIn("checks", report)
            self.assertIn("version", report)
            self.assertGreater(len(report["checks"]), 3)

    def test_edr_process_collection(self):
        processes = collect_running_processes(limit=5)
        self.assertIsInstance(processes, list)
        events = suspicious_process_events(
            [{"comm": "mimikatz", "args": "test", "pid": "1", "user": "root"}]
        )
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "process_alert")

    def test_nmap_probe_graceful_without_nmap(self):
        if not nmap_available():
            result = scan_host_ports("127.0.0.1")
            self.assertFalse(result["available"])


if __name__ == "__main__":
    unittest.main()

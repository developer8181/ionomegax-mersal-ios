# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
import os
import tempfile
import unittest
from pathlib import Path

from xig.core import EndpointEvent
from xig.fabric import MersalSecurityFabric, compute_posture
from xig.threat_feeds.stix import parse_stix_bundle
from xig.threat_feeds.feeds import MERSAL_GLOBAL_STIX
from xig.vuln import VulnerabilityScanner
from xig.storage import Database


class FabricTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        os.environ["MERSAL_KEV_FEED_URL"] = ""
        self.db = Database(Path(self.tmpdir.name) / "fabric.sqlite3")
        self.db.init_schema()
        self.db.seed_demo()
        self.fabric = MersalSecurityFabric(self.db)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_stix_bundle_parses_indicators(self):
        indicators = parse_stix_bundle(MERSAL_GLOBAL_STIX)
        self.assertGreaterEqual(len(indicators), 2)

    def test_threat_feed_sync(self):
        result = self.fabric.feeds.sync_all()
        self.assertGreater(result["indicators_added"], 0)
        self.assertGreaterEqual(len(self.db.list_threat_intel()), 5)

    def test_vulnerability_scan_records_findings(self):
        self.db.record_agent_heartbeat(
            agent_id="scan-agent",
            agent_type="endpoint",
            hostname="scan-host",
            os_name="Linux",
            metadata={
                "endpoint_id": "scan-host",
                "vuln_probe": {"open_ports": [445, 3389], "listening_ports": [{"local": "0.0.0.0:445"}]},
                "security_features": {"disk_encryption": False},
            },
        )
        result = VulnerabilityScanner(self.db).scan_all_endpoints(scope="test")
        self.assertGreaterEqual(result["findings_count"], 1)
        open_findings = self.db.list_vuln_findings(status="open")
        self.assertTrue(open_findings)

    def test_daily_cycle_runs_jobs(self):
        results = self.fabric.run_daily_now()
        self.assertIn("threat_feeds", results)
        self.assertIn("vuln_scan", results)
        self.assertIn("posture", results)
        posture = self.db.latest_security_posture()
        self.assertGreaterEqual(int(posture["score"]), 0)

    def test_soar_triggers_on_ai_escalated_event(self):
        event = EndpointEvent(
            endpoint_id="soar-ep-1",
            actor="tester",
            event_type="network_upload",
            channel="unsanctioned_cloud",
            resource="/tmp/x.zip",
            classification="confidential",
            destination="https://pastebin.com/raw/xyz",
            severity=25,
        )
        self.db.ingest_event(event)
        runs = self.db.list_soar_runs()
        self.assertTrue(runs)

    def test_fabric_dashboard(self):
        dashboard = self.fabric.dashboard()
        self.assertEqual(dashboard["fabric"], "Mersal Global Security Fabric")
        self.assertIn("posture", dashboard)
        self.assertIn("vulnerabilities", dashboard)


if __name__ == "__main__":
    unittest.main()

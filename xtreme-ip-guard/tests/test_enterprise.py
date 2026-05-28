# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

import tempfile
import unittest
from pathlib import Path

from xig.compliance import ComplianceEngine
from xig.core import EndpointEvent
from xig.enterprise import MersalEnterpriseSuite
from xig.fabric import MersalSecurityFabric
from xig.siem import SiemCorrelator
from xig.storage import Database


class EnterpriseTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmpdir.name) / "enterprise.sqlite3")
        self.db.init_schema()
        self.db.seed_demo()
        self.fabric = MersalSecurityFabric(self.db)
        self.suite = MersalEnterpriseSuite(self.db, fabric=self.fabric)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_siem_alert_on_credential_event(self):
        event = EndpointEvent(
            endpoint_id="endpoint-demo-001",
            actor="tester",
            event_type="network_upload",
            channel="unsanctioned_cloud",
            resource="/tmp/creds.zip",
            classification="credential",
            destination="https://evil.example/leak",
            severity=40,
        )
        row = self.db.ingest_event(event)
        alerts = self.db.list_siem_alerts()
        self.assertTrue(alerts)
        self.assertGreaterEqual(int(row["risk_score"]), 0)

    def test_compliance_assessment(self):
        result = ComplianceEngine(self.db).assess()
        self.assertGreaterEqual(int(result["score"]), 0)
        self.assertGreaterEqual(int(result["total"]), 1)

    def test_enterprise_dashboard(self):
        dash = self.suite.dashboard()
        self.assertEqual(dash["suite"], "Mersal Enterprise Security Suite")
        self.assertIn("siem", dash["modules"])
        self.assertIn("compliance", dash["modules"])

    def test_comparison_matrix(self):
        matrix = self.suite.comparison_matrix()
        self.assertGreaterEqual(len(matrix), 5)

    def test_siem_retrospective(self):
        correlator = SiemCorrelator(self.db)
        result = correlator.run_retrospective(limit=20)
        self.assertIn("events_scanned", result)

    def test_enterprise_cycle(self):
        lite = MersalEnterpriseSuite(self.db, fabric=None)
        result = lite.run_enterprise_cycle()
        self.assertIn("compliance", result)
        self.assertIn("network_policy", result)


if __name__ == "__main__":
    unittest.main()

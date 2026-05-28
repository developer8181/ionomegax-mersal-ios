# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
import tempfile
import unittest
from pathlib import Path

from xig.ai import MersalAICortex
from xig.ai.threat_intel import DEFAULT_IOCS
from xig.core import EndpointEvent
from xig.storage import Database


class AICortexTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmpdir.name) / "ai.sqlite3")
        self.db.init_schema()
        self.db.seed_demo()
        self.cortex = MersalAICortex(self.db)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_ioc_match_escalates_to_block(self):
        event = EndpointEvent(
            endpoint_id="ai-laptop-01",
            actor="tester",
            event_type="network_upload",
            channel="unsanctioned_cloud",
            resource="/tmp/data.zip",
            classification="confidential",
            destination="https://pastebin.com/raw/abc",
            severity=20,
        )
        stored = self.db.ingest_event(event)
        self.assertIn(stored["action"], {"block", "isolate_endpoint"})
        self.assertIn("ai-escalated", stored["tags"])
        ai_meta = stored["metadata"].get("ai", {})
        self.assertTrue(ai_meta.get("ioc_hits"))
        self.assertIn("pastebin.com", ai_meta["ioc_hits"][0].get("indicator", ""))

    def test_dashboard_returns_engine_metadata(self):
        event = EndpointEvent(
            endpoint_id="ai-laptop-02",
            actor="tester",
            event_type="file_copy",
            channel="removable_media",
            resource="/secret.doc",
            classification="secret",
            destination="usb",
            severity=30,
        )
        self.db.ingest_event(event)
        dashboard = self.cortex.dashboard()
        self.assertEqual(dashboard["engine"], "Mersal Neural Cortex")
        self.assertGreaterEqual(dashboard["baseline_signals"], 1)
        self.assertTrue(dashboard["recent_insights"])

    def test_train_from_history_builds_baselines(self):
        for index in range(6):
            self.db.ingest_event(
                EndpointEvent(
                    endpoint_id="train-ep",
                    actor="ops",
                    event_type="file_copy",
                    channel="local_file",
                    resource=f"/docs/file-{index}.txt",
                    classification="internal",
                    destination="",
                    severity=5 + index,
                )
            )
        result = self.db.train_cortex_from_history(limit=10)
        self.assertGreaterEqual(result["trained_samples"], 6)
        self.assertGreaterEqual(result["baseline_signals"], 1)

    def test_seed_threat_intel(self):
        inserted = self.db.seed_threat_intel(DEFAULT_IOCS)
        self.assertGreater(inserted, 0)
        self.assertGreaterEqual(len(self.db.list_threat_intel()), len(DEFAULT_IOCS))


if __name__ == "__main__":
    unittest.main()

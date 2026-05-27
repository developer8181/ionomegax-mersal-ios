import tempfile
import unittest
from pathlib import Path

from eipg.storage import Database


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.tmpdir.name) / "eipg.sqlite3")
        self.database.init_schema()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_records_asset_heartbeat_and_expands_json(self):
        asset = self.database.record_asset_heartbeat(
            asset_id="asset-001",
            hostname="analyst-laptop",
            owner="Analyst",
            ip_address="192.168.10.20",
            posture={"edr_enabled": False, "os_patch_age_days": 50, "sensitive_data_at_rest": True},
        )

        self.assertEqual(asset["asset_id"], "asset-001")
        self.assertEqual(asset["hostname"], "analyst-laptop")
        self.assertEqual(asset["risk_level"], "medium")
        self.assertIn("posture", asset)
        self.assertTrue(asset["ip_classification"]["is_private"])

    def test_records_dlp_event_against_asset(self):
        self.database.record_asset_heartbeat(asset_id="asset-002", hostname="finance-laptop")

        event = self.database.record_dlp_event(
            asset_ref="asset-002",
            username="sara",
            channel="external_upload",
            sensitivity="confidential",
            destination="personal-cloud.example",
            destination_trusted=False,
            bytes_count=2048,
        )

        self.assertFalse(event["allowed"])
        self.assertEqual(event["action"], "quarantine")
        self.assertEqual(event["asset_hostname"], "finance-laptop")

    def test_isolate_and_restore_asset(self):
        self.database.record_asset_heartbeat(asset_id="asset-003", hostname="server")

        isolated = self.database.isolate_asset("asset-003", actor="security-admin")
        restored = self.database.restore_asset("asset-003", actor="security-admin")

        self.assertEqual(isolated["status"], "isolated")
        self.assertEqual(restored["status"], "healthy")
        self.assertEqual(len(self.database.list_audit_log()), 3)

    def test_demo_seed_creates_assets_and_policies(self):
        self.database.seed_demo()

        self.assertGreaterEqual(len(self.database.list_assets()), 2)
        self.assertGreaterEqual(len(self.database.list_policies()), 4)


if __name__ == "__main__":
    unittest.main()


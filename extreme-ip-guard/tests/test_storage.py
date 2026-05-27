import tempfile
import unittest
from pathlib import Path

from eipg.storage import Database


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "test.sqlite3"
        self.db = Database(self.db_path)
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_evaluate_allows_registered_device_https(self):
        decision = self.db.evaluate(
            source_ip="10.0.1.50",
            destination_ip="8.8.8.8",
            destination_port=443,
            protocol="tcp",
            device_id="dev-laptop-001",
        )
        self.assertTrue(decision["allowed"])

    def test_evaluate_blocks_known_bad_ip(self):
        decision = self.db.evaluate(source_ip="203.0.113.50", destination_port=443)
        self.assertFalse(decision["allowed"])
        self.assertIn("Blocked", decision["reason"])

    def test_register_and_approve_device(self):
        device = self.db.register_device(
            device_id="dev-test-001",
            hostname="TEST-PC",
            ip_address="10.0.9.99",
            mac_address="aa:bb:cc:dd:ee:99",
            zone="default",
        )
        self.assertEqual(device["status"], "pending")
        approved = self.db.approve_device("dev-test-001")
        self.assertEqual(approved["status"], "approved")

    def test_auto_block_on_port_scan(self):
        attacker = "203.0.113.77"
        for port in range(20, 35):
            self.db.ingest_flow(
                source_ip=attacker,
                destination_ip="10.0.1.1",
                destination_port=port,
                protocol="tcp",
            )
        blocks = self.db.list_blocks()
        targets = [b["target"] for b in blocks]
        self.assertIn(attacker, targets)

    def test_policy_bundle_has_signature(self):
        bundle = self.db.get_policy_bundle()
        self.assertIn("signature", bundle)
        self.assertGreater(bundle["version"], 0)
        self.assertTrue(len(bundle["rules"]) > 0)

    def test_audit_chain_grows(self):
        self.db.register_device(device_id="audit-test", hostname="AUDIT")
        audit = self.db.list_audit()
        self.assertTrue(any(entry["event_type"] == "device.register" for entry in audit))


if __name__ == "__main__":
    unittest.main()

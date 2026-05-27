import tempfile
import unittest
from pathlib import Path

from xig.core import EndpointEvent
from xig.storage import Database


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmpdir.name) / "xig.sqlite3")
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_seed_demo_creates_initial_policy_and_endpoint(self):
        self.assertGreaterEqual(len(self.db.list_policies()), 4)
        endpoints = self.db.list_endpoints()

        self.assertEqual(endpoints[0]["endpoint_id"], "endpoint-demo-001")
        self.assertFalse(endpoints[0]["isolated"])

    def test_heartbeat_upserts_agent_and_endpoint(self):
        agent = self.db.record_agent_heartbeat(
            agent_id="xig-agent-laptop-001",
            agent_type="endpoint",
            hostname="laptop-001",
            os_name="Linux",
            version="0.1.0",
            metadata={"endpoint_id": "laptop-001", "owner": "sara"},
        )

        self.assertEqual(agent["agent_id"], "xig-agent-laptop-001")
        endpoint_ids = {endpoint["endpoint_id"] for endpoint in self.db.list_endpoints()}
        self.assertIn("laptop-001", endpoint_ids)

    def test_ingest_event_records_policy_decision(self):
        event = EndpointEvent(
            endpoint_id="laptop-001",
            actor="sara",
            event_type="file_copy",
            channel="removable_media",
            resource="/finance/payroll.xlsx",
            classification="secret",
            destination="usb:Kingston",
            severity=25,
        )
        stored = self.db.ingest_event(event)

        self.assertEqual(stored["action"], "block")
        self.assertEqual(stored["matched_rule_id"], "XIG-DLP-USB-SECRET")
        self.assertEqual(len(self.db.list_events()), 1)

    def test_credential_exfiltration_isolates_endpoint(self):
        event = EndpointEvent(
            endpoint_id="laptop-002",
            actor="omar",
            event_type="network_upload",
            channel="network_upload",
            resource="password-vault-export.csv",
            classification="credential",
            destination="http://unknown.example/upload",
            severity=40,
            behavior_flags=("mass_file_access",),
        )
        stored = self.db.ingest_event(event)
        endpoint = [item for item in self.db.list_endpoints() if item["endpoint_id"] == "laptop-002"][0]

        self.assertEqual(stored["action"], "isolate_endpoint")
        self.assertTrue(endpoint["isolated"])


if __name__ == "__main__":
    unittest.main()

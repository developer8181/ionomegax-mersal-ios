import tempfile
import unittest
from pathlib import Path

from xipg.storage import Database


class StorageWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tempdir.name) / "test.sqlite3")
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_low_risk_event_is_allowed_without_incident(self):
        asset = next(row for row in self.db.list_assets() if row["hostname"] == "soc-analyst-01")

        event = self.db.ingest_event(
            asset_id=asset["id"],
            source_ip="10.10.30.21",
            destination_ip="10.1.1.8",
            destination_port=443,
            protocol="tcp",
            country="SA",
            bytes_out=5_000,
            bytes_in=40_000,
            process_name="safari",
            ip_reputation_score=5,
            burst_connections=4,
        )

        self.assertEqual(event["action"], "allow")
        self.assertIsNone(event["incident_id"])
        self.assertEqual(len([row for row in self.db.list_incidents() if row["status"] == "open"]), 0)

    def test_high_risk_event_creates_incident_and_quarantines_asset(self):
        asset = next(row for row in self.db.list_assets() if row["hostname"] == "finance-laptop-07")

        event = self.db.ingest_event(
            asset_id=asset["id"],
            source_ip="10.10.20.17",
            destination_ip="203.0.113.45",
            destination_port=445,
            protocol="tcp",
            country="RU",
            bytes_out=75_000_000,
            bytes_in=500_000,
            process_name="powershell.exe",
            ip_reputation_score=96,
            tor_exit_node=True,
            geo_anomaly=True,
            burst_connections=900,
        )

        updated_asset = next(row for row in self.db.list_assets() if row["id"] == asset["id"])
        incidents = self.db.list_incidents()

        self.assertEqual(event["action"], "quarantine")
        self.assertIsNotNone(event["incident_id"])
        self.assertEqual(updated_asset["posture"], "quarantined")
        self.assertEqual(incidents[0]["status"], "open")

    def test_record_agent_heartbeat_upserts_metadata(self):
        first = self.db.record_agent_heartbeat(
            agent_id="sensor-finance-01",
            agent_type="sensor",
            hostname="finance-laptop-07",
            os_name="Windows 11",
            version="0.1.0",
            metadata={"control_profile": "windows-wfp"},
        )
        second = self.db.record_agent_heartbeat(
            agent_id="sensor-finance-01",
            agent_type="sensor",
            hostname="finance-laptop-07",
            os_name="Windows 11",
            version="0.1.1",
            metadata={"control_profile": "windows-wfp", "segment": "finance"},
        )

        self.assertEqual(first["agent_id"], "sensor-finance-01")
        self.assertEqual(second["version"], "0.1.1")
        self.assertEqual(second["metadata"]["segment"], "finance")
        self.assertEqual(len(self.db.list_agents()), 1)

    def test_resolve_incident_updates_status(self):
        asset = next(row for row in self.db.list_assets() if row["hostname"] == "finance-laptop-07")
        event = self.db.ingest_event(
            asset_id=asset["id"],
            source_ip="10.10.20.17",
            destination_ip="203.0.113.45",
            destination_port=445,
            protocol="tcp",
            country="RU",
            bytes_out=30_000_000,
            bytes_in=200_000,
            process_name="powershell.exe",
            ip_reputation_score=88,
            geo_anomaly=True,
            burst_connections=300,
        )

        resolved = self.db.resolve_incident(event["incident_id"], note="Validated and contained")

        self.assertEqual(resolved["status"], "resolved")
        self.assertEqual(resolved["resolution_note"], "Validated and contained")


if __name__ == "__main__":
    unittest.main()

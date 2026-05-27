import os
import tempfile
import unittest

from xig.core import EventKind, TelemetryEvent, utc_now_iso
from xig.storage import Database


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        self.tmp.close()
        os.unlink(self.tmp.name)
        self.db = Database(self.tmp.name)
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except FileNotFoundError:
            pass

    def test_seed_creates_users_and_assets(self):
        users = self.db.list_users()
        self.assertGreaterEqual(len(users), 4)
        assets = self.db.list_assets()
        self.assertGreaterEqual(len(assets), 3)

    def test_enrol_token_to_active_agent(self):
        token = self.db.issue_enrol_token(hostname="WS-TEST-01")["enrol_token"]
        result = self.db.enrol_agent(
            enrol_token=token,
            agent_id="agent-test-01",
            hw_fp="hwfp-test",
            os_name="Linux Test",
            version="0.1.0",
        )
        self.assertIn("agent_secret", result)
        self.assertGreater(result["policy_bundle"]["version"], 0)
        agents = self.db.list_agents()
        self.assertTrue(any(a["agent_id"] == "agent-test-01" for a in agents))

    def test_invalid_enrol_token_rejected(self):
        with self.assertRaises(ValueError):
            self.db.enrol_agent(
                enrol_token="bogus",
                agent_id="agent-bogus",
                hw_fp="x",
                os_name="x",
                version="0",
            )

    def test_event_ingest_creates_alerts_and_commands(self):
        token = self.db.issue_enrol_token(hostname="WS-TEST-02")["enrol_token"]
        self.db.enrol_agent(
            enrol_token=token,
            agent_id="agent-test-02",
            hw_fp="hwfp",
            os_name="x",
            version="0",
        )
        event = TelemetryEvent(
            agent_id="agent-test-02",
            kind=EventKind.FILE_WRITE.value,
            ts=utc_now_iso(),
            subject="usb",
            data={"path": "/media/usb/dump.zip", "bytes": 80_000_000},
        )
        result = self.db.ingest_event(event)
        self.assertTrue(any(a["rule_id"] == "R-USB-001" for a in result["alerts"]))
        self.assertTrue(any(c["playbook"] == "pb-usb-mass-copy" for c in result["commands_queued"]))

    def test_event_chain_and_audit_chain_intact(self):
        token = self.db.issue_enrol_token(hostname="WS-TEST-03")["enrol_token"]
        enrol = self.db.enrol_agent(
            enrol_token=token,
            agent_id="agent-test-03",
            hw_fp="hwfp",
            os_name="x",
            version="0",
        )
        self.db.ingest_event(
            TelemetryEvent(
                agent_id="agent-test-03",
                kind=EventKind.NETWORK_CONNECT.value,
                ts=utc_now_iso(),
                subject="net",
                data={"domain": "malware-c2.example", "ip": "203.0.113.66"},
            )
        )
        self.assertTrue(self.db.verify_event_chain()["intact"])
        self.assertTrue(self.db.verify_audit_chain()["intact"])
        self.assertGreater(enrol["policy_bundle"]["version"], 0)

    def test_authenticate_default_admin(self):
        user = self.db.authenticate("admin", "admin")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "admin")
        self.assertIsNone(self.db.authenticate("admin", "wrong"))

    def test_command_complete_round_trip(self):
        token = self.db.issue_enrol_token(hostname="WS-TEST-04")["enrol_token"]
        self.db.enrol_agent(
            enrol_token=token,
            agent_id="agent-test-04",
            hw_fp="hwfp",
            os_name="x",
            version="0",
        )
        self.db.ingest_event(
            TelemetryEvent(
                agent_id="agent-test-04",
                kind=EventKind.FILE_WRITE.value,
                ts=utc_now_iso(),
                subject="usb",
                data={"path": "/media/usb/exfil.zip", "bytes": 90_000_000},
            )
        )
        commands = self.db.fetch_pending_commands("agent-test-04")
        self.assertTrue(commands)
        result = self.db.complete_command(
            command_uid=commands[0]["command_uid"],
            status="succeeded",
            result={"ok": True},
            actor="agent:agent-test-04",
        )
        self.assertEqual(result["status"], "succeeded")

    def test_add_ioc_then_detect(self):
        token = self.db.issue_enrol_token(hostname="WS-TEST-05")["enrol_token"]
        self.db.enrol_agent(
            enrol_token=token,
            agent_id="agent-test-05",
            hw_fp="hwfp",
            os_name="x",
            version="0",
        )
        self.db.add_ioc(kind="domain", value="EVIL.example")
        result = self.db.ingest_event(
            TelemetryEvent(
                agent_id="agent-test-05",
                kind=EventKind.NETWORK_CONNECT.value,
                ts=utc_now_iso(),
                subject="net",
                data={"domain": "evil.example", "ip": "10.0.0.1"},
            )
        )
        self.assertTrue(any(a["rule_id"] == "R-NET-001" for a in result["alerts"]))


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from epms.core import money_to_cents
from epms.storage import Database


class StorageWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tempdir.name) / "test.sqlite3")
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_submit_allowed_job_charges_user(self):
        user = self.db.list_users()[0]
        printer = self.db.list_printers()[0]

        job = self.db.submit_job(
            user_id=user["id"],
            printer_id=printer["id"],
            document_name="policy.pdf",
            pages=2,
            copies=1,
            color=False,
            duplex=False,
            source="print-provider",
            agent_id="provider-1",
        )

        updated_user = next(row for row in self.db.list_users() if row["id"] == user["id"])
        self.assertEqual(job["status"], "printed")
        self.assertEqual(job["source"], "print-provider")
        self.assertEqual(job["agent_id"], "provider-1")
        self.assertEqual(updated_user["balance_cents"], user["balance_cents"] - job["cost_cents"])

    def test_hold_job_when_quota_is_insufficient(self):
        user = next(row for row in self.db.list_users() if row["username"] == "sara")
        printer = next(row for row in self.db.list_printers() if row["color_supported"])

        job = self.db.submit_job(
            user_id=user["id"],
            printer_id=printer["id"],
            document_name="large-color-book.pdf",
            pages=100,
            copies=1,
            color=True,
            duplex=False,
        )

        self.assertEqual(job["status"], "held")
        self.assertEqual(job["reason"], "Insufficient print quota")

    def test_add_credit_then_release_held_job(self):
        user = next(row for row in self.db.list_users() if row["username"] == "sara")
        printer = next(row for row in self.db.list_printers() if row["color_supported"])
        job = self.db.submit_job(
            user_id=user["id"],
            printer_id=printer["id"],
            document_name="medium-color-book.pdf",
            pages=40,
            copies=1,
            color=True,
            duplex=False,
        )

        self.db.add_credit(user["id"], money_to_cents("20.00"))
        released = self.db.release_job(job["id"])

        self.assertEqual(released["status"], "printed")
        self.assertEqual(released["reason"], "Released by administrator")

    def test_unsupported_color_job_is_denied_without_charge(self):
        user = self.db.list_users()[0]
        bw_printer = next(row for row in self.db.list_printers() if not row["color_supported"])

        job = self.db.submit_job(
            user_id=user["id"],
            printer_id=bw_printer["id"],
            document_name="poster.pdf",
            pages=1,
            copies=1,
            color=True,
            duplex=False,
        )

        updated_user = next(row for row in self.db.list_users() if row["id"] == user["id"])
        self.assertEqual(job["status"], "denied")
        self.assertEqual(updated_user["balance_cents"], user["balance_cents"])

    def test_record_agent_heartbeat_upserts_metadata(self):
        first = self.db.record_agent_heartbeat(
            agent_id="printer-controller-1",
            agent_type="printer-controller",
            hostname="mfd-gateway",
            os_name="embedded",
            version="0.1.0",
            metadata={"vendor": "hp", "platform": "OXP"},
        )
        second = self.db.record_agent_heartbeat(
            agent_id="printer-controller-1",
            agent_type="printer-controller",
            hostname="mfd-gateway",
            os_name="embedded",
            version="0.1.1",
            metadata={"vendor": "hp", "platform": "Workpath"},
        )

        self.assertEqual(first["agent_id"], "printer-controller-1")
        self.assertEqual(second["version"], "0.1.1")
        self.assertEqual(second["metadata"]["platform"], "Workpath")
        self.assertEqual(len(self.db.list_agents()), 1)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from epms.storage import Database


class ProductionStorageTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tempdir.name) / "epms.sqlite3", audit_retention_days=30)
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_bootstrap_admin_and_login(self):
        info = self.db.bootstrap_admin(password="StrongPass123")
        self.assertIsNotNone(info)
        token, user = self.db.authenticate_admin(username="admin", password="StrongPass123")
        self.assertTrue(token)
        self.assertEqual(user.role, "superadmin")
        resolved = self.db.resolve_session(token)
        self.assertIsNotNone(resolved)

    def test_department_pricing_changes_job_cost(self):
        self.db.upsert_pricing_rule(department="Students", bw_multiplier_percent=50, color_multiplier_percent=50)
        users = {row["username"]: row["id"] for row in self.db.list_users()}
        printers = {row["name"]: row["id"] for row in self.db.list_printers()}
        baseline = self.db.submit_job(
            user_id=users["itdesk"],
            printer_id=printers["Main Office HP"],
            document_name="baseline.pdf",
            pages=10,
            copies=1,
            color=False,
            duplex=False,
        )
        discounted = self.db.submit_job(
            user_id=users["sara"],
            printer_id=printers["Main Office HP"],
            document_name="student.pdf",
            pages=10,
            copies=1,
            color=False,
            duplex=False,
        )
        self.assertLess(discounted["cost_cents"], baseline["cost_cents"])

    def test_site_outbox_round_trip(self):
        item = self.db.enqueue_site_sync(
            site_id="branch-east",
            method="POST",
            path="/api/jobs",
            payload={"user_id": 1, "printer_id": 1, "pages": 1},
        )
        pending = self.db.list_site_outbox(site_id="branch-east", pending_only=True)
        self.assertEqual(len(pending), 1)
        self.db.mark_site_outbox_synced(int(item["id"]))
        self.assertEqual(len(self.db.list_site_outbox(site_id="branch-east", pending_only=True)), 0)


if __name__ == "__main__":
    unittest.main()

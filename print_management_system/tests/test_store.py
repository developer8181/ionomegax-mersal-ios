import tempfile
import unittest
from pathlib import Path

from print_mgmt import PrintManagementStore


class PrintManagementStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.store = PrintManagementStore(Path(self.tmpdir.name) / "test.sqlite3")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_submit_job_consumes_quota_when_queued(self):
        user = self.store.create_user("sara", "Sara", quota_pages=10)
        printer = self.store.create_printer("Office A", supports_color=True)

        job = self.store.submit_job(
            user_id=user["id"],
            printer_id=printer["id"],
            title="report.pdf",
            pages=3,
            copies=2,
            color=False,
            duplex=True,
        )

        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["charged_pages"], 6)
        self.assertEqual(job["estimated_sheets"], 4)
        updated_user = self.store.get_user(user["id"])
        self.assertEqual(updated_user["used_pages"], 6)
        self.assertEqual(updated_user["remaining_pages"], 4)

    def test_submit_job_rejects_when_quota_is_not_enough(self):
        user = self.store.create_user("omar", quota_pages=3)
        printer = self.store.create_printer("Office B", supports_color=True)

        job = self.store.submit_job(
            user_id=user["id"],
            printer_id=printer["id"],
            title="large.pdf",
            pages=4,
        )

        self.assertEqual(job["status"], "rejected")
        self.assertEqual(job["reason"], "quota_exceeded")
        self.assertEqual(self.store.get_user(user["id"])["used_pages"], 0)

    def test_submit_job_rejects_color_on_black_and_white_printer(self):
        user = self.store.create_user("nora", quota_pages=20)
        printer = self.store.create_printer("Reception", supports_color=False)

        job = self.store.submit_job(
            user_id=user["id"],
            printer_id=printer["id"],
            title="flyer.pdf",
            pages=2,
            color=True,
        )

        self.assertEqual(job["status"], "rejected")
        self.assertEqual(job["reason"], "printer_does_not_support_color")
        self.assertEqual(self.store.get_user(user["id"])["used_pages"], 0)

    def test_cancel_job_refunds_quota(self):
        user = self.store.create_user("ali", quota_pages=10)
        printer = self.store.create_printer("Lab")
        job = self.store.submit_job(
            user_id=user["id"],
            printer_id=printer["id"],
            title="assignment.pdf",
            pages=5,
        )

        cancelled = self.store.update_job_status(job["id"], "cancelled")

        self.assertEqual(cancelled["status"], "cancelled")
        self.assertEqual(self.store.get_user(user["id"])["used_pages"], 0)

    def test_release_job_keeps_quota_consumed(self):
        user = self.store.create_user("mona", quota_pages=10)
        printer = self.store.create_printer("Library")
        job = self.store.submit_job(
            user_id=user["id"],
            printer_id=printer["id"],
            title="slides.pdf",
            pages=5,
        )

        released = self.store.update_job_status(job["id"], "released")

        self.assertEqual(released["status"], "released")
        self.assertEqual(self.store.get_user(user["id"])["used_pages"], 5)


if __name__ == "__main__":
    unittest.main()

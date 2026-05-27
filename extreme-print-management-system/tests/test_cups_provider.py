import tempfile
import unittest
from pathlib import Path

from epms.cups_provider import SeenJobStore, cups_job_to_spool_event, discover_cups_printers, list_cups_jobs


class CupsProviderTests(unittest.TestCase):
    def test_discovers_cups_printers_from_lpstat_output(self):
        printers = discover_cups_printers(
            """
            printer HQ_SecurePrint_Cluster is idle. enabled since Wed 27 May 2026 10:00:00 AM UTC
            printer Archive_Kyocera_HyPAS disabled since Wed 27 May 2026 10:01:00 AM UTC -
            """
        )

        self.assertEqual(printers[0].queue_name, "HQ_SecurePrint_Cluster")
        self.assertTrue(printers[0].enabled)
        self.assertEqual(printers[1].status, "disabled")
        self.assertFalse(printers[1].enabled)

    def test_lists_cups_jobs_from_lpstat_output(self):
        jobs = list_cups_jobs(
            """
            HQ_SecurePrint_Cluster-42 finance 20480 Wed May 27 16:20:10 2026
            Library_BW_Fleet-43 student-a 1024 Wed May 27 16:21:11 2026
            """
        )

        self.assertEqual(jobs[0].queue_name, "HQ_SecurePrint_Cluster")
        self.assertEqual(jobs[0].job_ref, "HQ_SecurePrint_Cluster-42")
        self.assertEqual(jobs[0].username, "finance")
        self.assertEqual(jobs[1].size_bytes, 1024)

    def test_maps_cups_job_to_spool_event(self):
        job = list_cups_jobs("HQ_SecurePrint_Cluster-42 finance 20480 Wed May 27 16:20:10 2026")[0]
        event = cups_job_to_spool_event(
            job,
            user_map={"finance": 2},
            printer_map={"HQ_SecurePrint_Cluster": 1},
            default_pages=3,
            account="Finance",
            agent_id="print-provider-hq",
        )

        payload = event.to_job_payload()
        self.assertEqual(payload["user_id"], 2)
        self.assertEqual(payload["printer_id"], 1)
        self.assertEqual(payload["pages"], 3)
        self.assertEqual(payload["spool_id"], "HQ_SecurePrint_Cluster-42")

    def test_seen_job_store_round_trip(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SeenJobStore(Path(tempdir) / "seen.json")
            self.assertEqual(store.read(), set())

            store.write({"queue-1", "queue-2"})
            self.assertEqual(store.read(), {"queue-1", "queue-2"})


if __name__ == "__main__":
    unittest.main()

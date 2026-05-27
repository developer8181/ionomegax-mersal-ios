import tempfile
import unittest
from pathlib import Path

from epms.print_provider import OfflineQueue, parse_spool_event


class PrintProviderTests(unittest.TestCase):
    def test_parse_spool_event_builds_job_payload(self):
        event = parse_spool_event(
            {
                "user_id": "1",
                "printer_id": "2",
                "document_name": "  ",
                "pages": "4",
                "copies": "2",
                "color": True,
                "duplex": True,
                "account": "",
                "spool_id": "cups-123",
            },
            default_agent_id="provider-1",
        )

        payload = event.to_job_payload()
        self.assertEqual(payload["document_name"], "Untitled document")
        self.assertEqual(payload["account"], "Personal")
        self.assertEqual(payload["agent_id"], "provider-1")
        self.assertEqual(payload["spool_id"], "cups-123")

    def test_parse_spool_event_rejects_invalid_counts(self):
        event = parse_spool_event(
            {"user_id": 1, "printer_id": 1, "document_name": "bad.pdf", "pages": 0},
        )

        with self.assertRaises(ValueError):
            event.to_job_payload()

    def test_offline_queue_round_trip_and_clear(self):
        with tempfile.TemporaryDirectory() as tempdir:
            queue = OfflineQueue(Path(tempdir) / "offline.jsonl")
            queue.enqueue({"document_name": "a.pdf", "pages": 1})
            queue.enqueue({"document_name": "b.pdf", "pages": 2})

            self.assertEqual(queue.count(), 2)
            self.assertEqual(queue.read_all()[1]["document_name"], "b.pdf")

            queue.replace([{"document_name": "c.pdf", "pages": 3}])
            self.assertEqual(queue.count(), 1)
            self.assertEqual(queue.read_all()[0]["pages"], 3)

            queue.clear()
            self.assertEqual(queue.count(), 0)


if __name__ == "__main__":
    unittest.main()

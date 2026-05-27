import unittest

from epms.windows_provider import parse_print_jobs, windows_job_to_spool_event


class WindowsProviderTests(unittest.TestCase):
    def test_parse_print_jobs(self):
        output = """
        Id User Document Pages Status
        12 finance Invoice-Q1.pdf 4 Printing
        """
        jobs = parse_print_jobs(output, queue_name="HQ_Printer")
        self.assertEqual(jobs[0].username, "finance")
        self.assertEqual(jobs[0].pages, 4)

    def test_map_to_spool_event(self):
        jobs = parse_print_jobs("12 finance Invoice-Q1.pdf 4 Printing", queue_name="HQ_Printer")
        event = windows_job_to_spool_event(
            jobs[0],
            user_map={"finance": 2},
            printer_map={"HQ_Printer": 1},
            account="Finance",
            agent_id="provider-win",
        )
        self.assertEqual(event.user_id, 2)
        self.assertEqual(event.spool_id, "win-HQ_Printer-12")


if __name__ == "__main__":
    unittest.main()

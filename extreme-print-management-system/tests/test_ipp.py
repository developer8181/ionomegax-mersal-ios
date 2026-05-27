import unittest

from epms.ipp_client import build_get_jobs_request, parse_get_jobs_response


class IppClientTests(unittest.TestCase):
    def test_build_get_jobs_request_has_ipp_version(self):
        payload = build_get_jobs_request(printer_uri="ipp://printer.local/ipp/print")
        self.assertTrue(payload.startswith(b"\x02\x00"))

    def test_parse_get_jobs_response_extracts_ids(self):
        sample = b"job-id\x0042job-name\x00invoice.pdfjob-state\x004"
        jobs = parse_get_jobs_response(sample)
        self.assertEqual(jobs[0].job_id, 42)
        self.assertIn("invoice", jobs[0].job_name)


if __name__ == "__main__":
    unittest.main()

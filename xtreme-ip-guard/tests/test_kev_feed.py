# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from xig.threat_feeds.feeds import ThreatFeedSync
from xig.vuln.kev_feed import fetch_kev_indicators
from xig.storage import Database


SAMPLE_KEV = {
    "vulnerabilities": [
        {
            "cveID": "CVE-2024-0001",
            "vendorProject": "Vendor",
            "product": "Product",
            "vulnerabilityName": "Test Vuln",
        }
    ]
}


class KevFeedTests(unittest.TestCase):
    def test_fetch_kev_parses_cve(self):
        payload = json.dumps(SAMPLE_KEV).encode()

        class FakeResponse:
            def read(self):
                return payload

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            indicators = fetch_kev_indicators("https://example.test/kev.json")
        self.assertEqual(len(indicators), 1)
        self.assertEqual(indicators[0]["indicator"], "cve-2024-0001")
        self.assertEqual(indicators[0]["source"], "cisa-kev")

    def test_threat_sync_includes_kev(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "kev.sqlite3")
            db.init_schema()
            with patch("xig.threat_feeds.feeds.fetch_kev_indicators") as mock_kev:
                mock_kev.return_value = [
                    {"indicator": "cve-2024-9999", "ioc_type": "cve", "severity": 90, "source": "cisa-kev"}
                ]
                result = ThreatFeedSync(db).sync_all(kev_url="https://example.test/kev.json")
            self.assertIn("cisa-kev", result["feeds"])
            self.assertGreater(result["indicators_added"], 0)


if __name__ == "__main__":
    unittest.main()

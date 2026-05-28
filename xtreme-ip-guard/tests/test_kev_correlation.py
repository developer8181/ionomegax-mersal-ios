# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

import tempfile
import unittest
from pathlib import Path

from xig.storage import Database
from xig.vuln.kev_correlation import apply_kev_priority, load_kev_cves


class KevCorrelationTests(unittest.TestCase):
    def test_apply_kev_priority(self):
        title, severity, flagged = apply_kev_priority(
            cve_id="CVE-2017-0144",
            title="SMB RCE",
            severity=8.0,
            kev_cves={"CVE-2017-0144"},
        )
        self.assertTrue(flagged)
        self.assertIn("CISA KEV", title)
        self.assertGreaterEqual(severity, 9.5)

    def test_load_kev_from_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "kev.sqlite3")
            db.init_schema()
            db.seed_threat_intel(
                [
                    {
                        "indicator": "cve-2017-0144",
                        "ioc_type": "cve",
                        "severity": 95,
                        "source": "cisa-kev",
                    }
                ]
            )
            kev = load_kev_cves(db)
            self.assertIn("CVE-2017-0144", kev)


if __name__ == "__main__":
    unittest.main()

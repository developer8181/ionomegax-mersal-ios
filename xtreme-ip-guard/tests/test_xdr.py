# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

import tempfile
import unittest
from pathlib import Path

from xig.logvault import LogVault
from xig.siem.suricata import parse_eve_line
from xig.storage import Database
from xig.xdr import XdrEngine


class XdrExpansionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "xdr.sqlite3")
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self):
        self.tmp.cleanup()

    def test_logvault_ingest_search(self):
        vault = LogVault(self.db)
        vault.ingest_batch([{"source": "test", "message": "failed login admin", "severity": 60}])
        hits = vault.search(query="login")
        self.assertEqual(len(hits), 1)

    def test_suricata_parse_eve(self):
        line = (
            '{"timestamp":"2026-01-01T00:00:00","event_type":"alert",'
            '"src_ip":"1.2.3.4","dest_ip":"5.6.7.8","proto":"TCP",'
            '"alert":{"signature_id":123,"signature":"ET TROJAN","category":"trojan-activity","severity":2}}'
        )
        parsed = parse_eve_line(line)
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["signature_id"], 123)

    def test_xdr_correlation_multi_signal(self):
        self.db.create_siem_alert(
            rule_id="SIEM-TEST",
            title="Test",
            severity=85,
            endpoint_id="endpoint-demo-001",
        )
        self.db.record_edr_detection(
            endpoint_id="endpoint-demo-001",
            detection_type="process",
            severity=80,
            title="EDR test",
        )
        result = XdrEngine(self.db).run_correlation()
        self.assertGreaterEqual(result["findings_created"], 1)
        self.assertGreater(len(self.db.list_xdr_findings()), 0)


if __name__ == "__main__":
    unittest.main()

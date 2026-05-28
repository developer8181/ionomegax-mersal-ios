# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import tempfile
import unittest
from unittest.mock import patch

from xig.compliance.evidence_pack import ComplianceEvidencePack
from xig.platform_ops.reliability_engine import ReliabilityEngine
from xig.security.session_policy import session_ttl_seconds
from xig.storage import Database


class V89ReliabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(self.tmp.name + "/rel.sqlite3")
        self.db.init_schema()
        self.db.ensure_rbac_seed()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_reliability_report(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MERSAL_PRODUCTION": "1",
                "MERSAL_SIGNING_SECRET": "x" * 48,
                "MERSAL_API_TOKEN": "token-32-chars-minimum-for-tests",
            },
            clear=False,
        ):
            report = ReliabilityEngine(self.db).full_report()
            self.assertIn("trust_score", report)
            self.assertIn("sla_tier", report)
            self.assertIn("dependable_for_operations", report)

    def test_evidence_pack_integrity(self) -> None:
        pack = ComplianceEvidencePack(self.db).build()
        self.assertIn("integrity_sha256", pack)
        self.assertTrue(len(pack["integrity_sha256"]) == 64)

    def test_session_ttl_enterprise(self) -> None:
        with patch.dict(os.environ, {"MERSAL_ENTERPRISE": "1", "MERSAL_PRODUCTION": "1"}, clear=False):
            self.assertEqual(session_ttl_seconds(), 28_800)

    def test_stale_agent_list_after_heartbeat(self) -> None:
        self.db.record_agent_heartbeat(
            agent_id="fresh-agent",
            agent_type="endpoint",
            hostname="fresh-host",
            metadata={"endpoint_id": "fresh-host"},
        )
        stale = self.db.list_stale_agents(threshold_seconds=60)
        self.assertEqual(len(stale), 0)


if __name__ == "__main__":
    unittest.main()

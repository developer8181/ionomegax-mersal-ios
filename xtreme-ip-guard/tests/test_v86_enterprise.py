# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import tempfile
import unittest
from unittest.mock import patch

from xig.integrations.siem_forwarder import SiemForwarder
from xig.platform_ops.enterprise_readiness import enterprise_adoption_report
from xig.platform_ops.postgres_health import postgres_cluster_health
from xig.storage import Database


class V86EnterpriseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(self.tmp.name + "/v86.sqlite3")
        self.db.init_schema()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_postgres_health_sqlite_mode(self) -> None:
        with patch.dict(os.environ, {"MERSAL_POSTGRES_DSN": ""}, clear=False):
            health = postgres_cluster_health()
            self.assertFalse(health["active"])

    def test_enterprise_adoption_report(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MERSAL_PRODUCTION": "1",
                "MERSAL_ENTERPRISE": "1",
                "MERSAL_SIGNING_SECRET": "x" * 48,
                "MERSAL_API_TOKEN": "test-token-32-chars-minimum-length",
            },
            clear=False,
        ):
            report = enterprise_adoption_report(self.db)
            self.assertIn("tier", report)
            self.assertIn("score", report)
            self.assertIn("recommendations", report)

    def test_scim_token_mint(self) -> None:
        created = self.db.create_scim_token(label="test-idp")
        self.assertTrue(created["token"].startswith("scim_"))
        self.assertTrue(self.db.verify_scim_token(created["token"]))
        listed = self.db.list_scim_tokens()
        self.assertEqual(len(listed), 1)

    def test_siem_forwarder_supports_tls_proto(self) -> None:
        source = SiemForwarder._send.__doc__  # noqa: SLF001
        self.assertIsNone(source)
        import inspect

        code = inspect.getsource(SiemForwarder._send)
        self.assertIn("syslog_tls", code)


if __name__ == "__main__":
    unittest.main()

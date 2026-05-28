# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import tempfile
import unittest

from xig.fabric import MersalSecurityFabric
from xig.rbac import RbacEngine
from xig.reporting import ReportExporter
from xig.siem.window_correlator import WindowCorrelator
from xig.storage import Database
from xig.tenant import TenantManager


class GlobalPlatformV6Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self._tmp.close()
        os.environ["MERSAL_ADMIN_PASSWORD"] = "test-secret"
        self.db = Database(self._tmp.name)
        self.db.init_schema()
        self.db.ensure_rbac_seed()
        self.fabric = MersalSecurityFabric(self.db)
        self.global_platform = self.fabric.global_platform

    def tearDown(self) -> None:
        os.unlink(self._tmp.name)

    def test_tenant_create(self) -> None:
        tenant = TenantManager(self.db).create("Acme Corp", slug="acme")
        self.assertTrue(tenant["tenant_id"].startswith("tenant-"))

    def test_rbac_authenticate(self) -> None:
        user = RbacEngine(self.db).authenticate("admin", "test-secret")
        self.assertIsNotNone(user)
        self.assertEqual(user["role"], "super_admin")

    def test_window_correlator_rules(self) -> None:
        rules = self.db.list_window_rules()
        self.assertGreaterEqual(len(rules), 3)

    def test_extended_compliance(self) -> None:
        result = self.global_platform.grc.assess_all()
        self.assertIn("NIST-CSF", result)
        self.assertIn("ISO27001", result)
        self.assertIn("SOC2", result)

    def test_report_export(self) -> None:
        csv_data = ReportExporter(self.db).export_csv("executive")
        self.assertIn("Executive Summary", csv_data)

    def test_global_matrix(self) -> None:
        matrix = self.global_platform.comparison_matrix()
        caps = {row["capability"] for row in matrix}
        self.assertIn("Multi-tenant / MSP", caps)

    def test_global_cycle(self) -> None:
        os.environ["MERSAL_KEV_FEED_URL"] = ""
        result = self.global_platform.run_global_cycle()
        self.assertIn("grc", result)


if __name__ == "__main__":
    unittest.main()

# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import tempfile
import unittest
from unittest.mock import patch

from xig.platform_ops.unified_platform import UnifiedPlatformController
from xig.storage import Database


class V87UnifiedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(self.tmp.name + "/unified.sqlite3")
        self.db.init_schema()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_bootstrap_enterprise(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MERSAL_SIGNING_SECRET": "x" * 48,
                "MERSAL_API_TOKEN": "test-token-minimum-32-characters-long",
            },
            clear=False,
        ):
            ctrl = UnifiedPlatformController(self.db)
            result = ctrl.bootstrap_enterprise(tenant_id="default")
            self.assertTrue(result["ok"])
            self.assertIn("steps", result)

    def test_full_dashboard(self) -> None:
        ctrl = UnifiedPlatformController(self.db)
        dash = ctrl.full_dashboard()
        self.assertEqual(dash["version"], "1.0.0")
        self.assertIn("capabilities", dash)
        self.assertGreater(len(dash["capabilities"]), 10)

    def test_complete_cycle_without_fabric(self) -> None:
        ctrl = UnifiedPlatformController(self.db)
        result = ctrl.run_complete_cycle()
        self.assertIn("backup", result)
        self.assertIn("fabric_daily", result)


if __name__ == "__main__":
    unittest.main()

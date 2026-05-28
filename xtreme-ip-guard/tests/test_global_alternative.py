# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import tempfile
import unittest
from unittest.mock import patch

from xig.platform_ops.global_alternative import (
    GlobalAlternativeController,
    _parity_index,
    parity_matrix,
    recommended_production_env,
)
from xig.storage import Database


class GlobalAlternativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(self.tmp.name + "/ga.sqlite3")
        self.db.init_schema()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_parity_matrix_nonempty(self) -> None:
        matrix = parity_matrix()
        self.assertGreaterEqual(len(matrix), 15)
        self.assertIn("parity", matrix[0])
        self.assertIn("ecs", matrix[0])

    def test_parity_index_high(self) -> None:
        index = _parity_index(parity_matrix())
        self.assertGreaterEqual(index, 70)

    def test_summary(self) -> None:
        summary = GlobalAlternativeController(self.db).summary()
        self.assertEqual(summary["version"], "1.1.0")
        self.assertGreaterEqual(summary["parity_index"], 70)
        self.assertIn("honest_limits", summary)

    def test_activate(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MERSAL_SIGNING_SECRET": "x" * 48,
                "MERSAL_API_TOKEN": "test-token-minimum-32-characters-long",
                "MERSAL_KEV_FEED_URL": "",
                "MERSAL_NO_SCHEDULER": "1",
            },
            clear=False,
        ):
            result = GlobalAlternativeController(self.db).activate(tenant_id="default")
            self.assertTrue(result["ok"])
            self.assertIn("evidence_pack", result["steps"])

    def test_recommended_env(self) -> None:
        env = recommended_production_env()
        self.assertIn("MERSAL_PRODUCTION", env)


if __name__ == "__main__":
    unittest.main()

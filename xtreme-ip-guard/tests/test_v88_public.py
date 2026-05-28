# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import unittest

from xig.platform_ops.public_summary import public_platform_summary


class V88PublicTests(unittest.TestCase):
    def test_public_summary(self) -> None:
        summary = public_platform_summary()
        self.assertEqual(summary["version"], "8.9.0")
        self.assertIn("api", summary)


if __name__ == "__main__":
    unittest.main()

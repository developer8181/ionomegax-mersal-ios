# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
import unittest

from xig.credits import COPYRIGHT_YEARS, system_about


class CreditsTests(unittest.TestCase):
    def test_system_about_bilingual(self):
        payload = system_about(version="2.0.0")
        self.assertIn("2009", COPYRIGHT_YEARS)
        self.assertIn("محمود", payload["ar"]["authorship"])
        self.assertIn("Mahmoud", payload["en"]["authorship"])
        self.assertIn("Ramallah", payload["en"]["company"])


if __name__ == "__main__":
    unittest.main()

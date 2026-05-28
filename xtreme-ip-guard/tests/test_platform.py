# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
import unittest

from xig.platform import collect_profile, collect_sensor_events


class PlatformTests(unittest.TestCase):
    def test_collect_profile_has_capabilities(self):
        profile = collect_profile()
        self.assertIn(profile.platform_id, {"linux", "windows", "darwin"})
        self.assertTrue(profile.capabilities)
        self.assertTrue(profile.hostname)

    def test_collect_sensor_events_returns_list(self):
        events = collect_sensor_events()
        self.assertIsInstance(events, list)


if __name__ == "__main__":
    unittest.main()

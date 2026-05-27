import unittest

from eig.anomaly import AnomalyEngine


class AnomalyTests(unittest.TestCase):
    def test_off_hours_anomaly(self) -> None:
        engine = AnomalyEngine()
        for day in range(5):
            for hour in range(9, 18):
                engine.record(
                    "user1",
                    category="web",
                    timestamp=f"2026-05-{20 + day:02d}T{hour:02d}:00:00+00:00",
                )
        result = engine.score("user1", category="dlp", timestamp="2026-05-27T03:00:00+00:00")
        self.assertGreaterEqual(result["score"], 30)
        self.assertTrue(result["is_anomalous"])


if __name__ == "__main__":
    unittest.main()

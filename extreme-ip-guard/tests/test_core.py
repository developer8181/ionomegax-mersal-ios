import unittest

from xig.core import (
    Severity,
    TelemetryEvent,
    blend_risk,
    canonical_json,
    classify_risk,
    mitre_lookup,
    normalize_iocs,
    severity_at_least,
)


class CoreTests(unittest.TestCase):
    def test_severity_ordering(self):
        self.assertLess(Severity.INFO.numeric, Severity.HIGH.numeric)
        self.assertTrue(severity_at_least("critical", Severity.HIGH))
        self.assertFalse(severity_at_least("low", Severity.HIGH))

    def test_blend_risk_caps_and_floors(self):
        self.assertEqual(blend_risk(-5, 10), 2.0)
        self.assertLessEqual(blend_risk(100, 100), 100.0)
        self.assertGreater(blend_risk(0, 50), 0)

    def test_classify_risk_bands(self):
        self.assertEqual(classify_risk(0), Severity.INFO)
        self.assertEqual(classify_risk(20), Severity.LOW)
        self.assertEqual(classify_risk(40), Severity.MEDIUM)
        self.assertEqual(classify_risk(65), Severity.HIGH)
        self.assertEqual(classify_risk(95), Severity.CRITICAL)

    def test_canonical_json_is_deterministic(self):
        a = canonical_json({"b": 1, "a": [3, 2, 1]})
        b = canonical_json({"a": [3, 2, 1], "b": 1})
        self.assertEqual(a, b)

    def test_mitre_lookup_returns_known(self):
        self.assertIn("name", mitre_lookup("T1059"))
        self.assertEqual(mitre_lookup("NOT-REAL"), {})

    def test_normalize_iocs_dedupes_and_lowers(self):
        self.assertEqual(
            normalize_iocs([" ABC.com ", "abc.COM", "abc.com", ""]),
            ["abc.com"],
        )

    def test_telemetry_event_validation(self):
        good = TelemetryEvent(agent_id="a", kind="file.write", ts="2025-01-01T00:00:00Z", subject="s")
        good.validate()
        bad = TelemetryEvent(agent_id="", kind="file.write", ts="2025-01-01T00:00:00Z", subject="s")
        with self.assertRaises(ValueError):
            bad.validate()
        bad_kind = TelemetryEvent(agent_id="a", kind="bogus", ts="2025-01-01T00:00:00Z", subject="s")
        with self.assertRaises(ValueError):
            bad_kind.validate()


if __name__ == "__main__":
    unittest.main()

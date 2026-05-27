import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from risk_engine import Decision, ExtremeIPGuardEngine, PolicyProfile, RiskSignal


class RiskEngineTests(unittest.TestCase):
    def test_low_risk_signal_is_allowed(self) -> None:
        engine = ExtremeIPGuardEngine()
        signal = RiskSignal(
            ip="198.51.100.10",
            intel_score=5,
            failed_auth_attempts=0,
            requests_per_minute=20,
            geo_velocity_kmph=0,
            impossible_travel=False,
            tor_exit_node=False,
            known_botnet=False,
            device_trust_score=90,
            endpoint_sensitivity=1,
        )

        result = engine.assess(signal)
        self.assertEqual(result.decision, Decision.ALLOW)
        self.assertLess(result.score, 45)

    def test_high_risk_signal_is_blocked(self) -> None:
        engine = ExtremeIPGuardEngine(policy=PolicyProfile.strict())
        signal = RiskSignal(
            ip="203.0.113.250",
            intel_score=95,
            failed_auth_attempts=12,
            requests_per_minute=420,
            geo_velocity_kmph=1100,
            impossible_travel=True,
            tor_exit_node=True,
            known_botnet=True,
            device_trust_score=10,
            endpoint_sensitivity=3,
        )

        result = engine.assess(signal)
        self.assertEqual(result.decision, Decision.BLOCK)
        self.assertGreaterEqual(result.score, 78)
        self.assertIn("known_botnet_indicator", result.reasons)

    def test_medium_risk_signal_requires_control(self) -> None:
        engine = ExtremeIPGuardEngine()
        signal = RiskSignal(
            ip="203.0.113.90",
            intel_score=52,
            failed_auth_attempts=4,
            requests_per_minute=110,
            geo_velocity_kmph=250,
            impossible_travel=False,
            tor_exit_node=False,
            known_botnet=False,
            device_trust_score=60,
            endpoint_sensitivity=2,
        )

        result = engine.assess(signal)
        self.assertIn(result.decision, {Decision.THROTTLE, Decision.CHALLENGE})
        self.assertGreaterEqual(result.score, 45)


if __name__ == "__main__":
    unittest.main()

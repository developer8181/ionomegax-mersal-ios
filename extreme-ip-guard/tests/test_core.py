import unittest

from eig.core import EnforcementAction, evaluate_event, composite_risk_score, zero_trust_session_verdict


class CoreTests(unittest.TestCase):
    def test_dlp_blocks_sensitive_keyword(self) -> None:
        decision = evaluate_event(
            category="dlp",
            summary="Email attachment",
            detail="Document marked TOP SECRET",
        )
        self.assertEqual(decision.action, EnforcementAction.WARN)
        self.assertTrue(decision.matched_rule_id)

    def test_network_port_scan_quarantine(self) -> None:
        decision = evaluate_event(
            category="network",
            summary="Port scan detected",
            detail="SYN flood against internal hosts",
        )
        self.assertEqual(decision.action, EnforcementAction.QUARANTINE)

    def test_composite_risk_elevated(self) -> None:
        profile = composite_risk_score(
            base_trust=40,
            recent_event_deltas=[30, 25, 20],
            anomaly_score=35,
        )
        self.assertGreaterEqual(profile.score, 65)
        self.assertIn("low_endpoint_trust", profile.factors)

    def test_zero_trust_denies_guest_without_mfa(self) -> None:
        verdict = zero_trust_session_verdict(
            device_posture={"encrypted_disk": True, "av_updated": True, "patch_level_ok": True, "agent_healthy": True},
            user_mfa=False,
            network_segment="guest",
        )
        self.assertFalse(verdict["granted"])


if __name__ == "__main__":
    unittest.main()

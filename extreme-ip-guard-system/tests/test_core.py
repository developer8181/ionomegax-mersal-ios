import unittest

from eipg.core import (
    AssetPosture,
    DlpEvent,
    classify_ip_address,
    evaluate_asset_posture,
    evaluate_dlp_event,
    risk_level_for_score,
)


class CoreRiskTests(unittest.TestCase):
    def test_low_risk_baseline_is_allowed(self):
        decision = evaluate_asset_posture(AssetPosture())

        self.assertEqual(decision.risk_score, 0)
        self.assertEqual(decision.risk_level, "low")
        self.assertEqual(decision.action, "allow")

    def test_critical_asset_is_recommended_for_isolation(self):
        decision = evaluate_asset_posture(
            AssetPosture(
                encryption_enabled=False,
                edr_enabled=False,
                firewall_enabled=False,
                os_patch_age_days=120,
                critical_vulns=3,
                high_vulns=6,
                failed_login_count=30,
                external_ip_exposure=True,
                unusual_egress_mb=2048,
            )
        )

        self.assertEqual(decision.risk_score, 100)
        self.assertEqual(decision.risk_level, "critical")
        self.assertEqual(decision.action, "isolate")

    def test_risk_level_boundaries(self):
        self.assertEqual(risk_level_for_score(34), "low")
        self.assertEqual(risk_level_for_score(35), "medium")
        self.assertEqual(risk_level_for_score(60), "high")
        self.assertEqual(risk_level_for_score(80), "critical")


class CoreDlpTests(unittest.TestCase):
    def test_secret_untrusted_destination_is_denied(self):
        decision = evaluate_dlp_event(
            DlpEvent(
                channel="external_upload",
                sensitivity="secret",
                destination_trusted=False,
                bytes_count=1024,
            )
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "deny")
        self.assertEqual(decision.severity, "critical")

    def test_encrypted_confidential_transfer_requires_approval(self):
        decision = evaluate_dlp_event(
            DlpEvent(
                channel="email",
                sensitivity="confidential",
                destination_trusted=False,
                bytes_count=4096,
                encrypted=True,
            )
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "require_approval")

    def test_public_data_is_allowed(self):
        decision = evaluate_dlp_event(DlpEvent(channel="web", sensitivity="public", destination_trusted=False))

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "allow")

    def test_ip_classification_is_passive(self):
        result = classify_ip_address("10.0.0.1")

        self.assertEqual(result["version"], "IPv4")
        self.assertTrue(result["is_private"])


if __name__ == "__main__":
    unittest.main()


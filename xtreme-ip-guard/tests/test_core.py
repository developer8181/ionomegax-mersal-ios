# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
import unittest

from xig.core import EndpointEvent, PolicyRule, calculate_risk_score, evaluate_event


class CorePolicyTests(unittest.TestCase):
    def test_secret_usb_copy_matches_block_policy(self):
        event = EndpointEvent(
            endpoint_id="laptop-001",
            actor="sara",
            event_type="file_copy",
            channel="removable_media",
            resource="/finance/payroll.xlsx",
            classification="secret",
            destination="usb:Kingston",
            severity=25,
        )
        decision = evaluate_event(
            event,
            [
                PolicyRule(
                    rule_id="XIG-DLP-USB-SECRET",
                    name="Block secret USB copy",
                    action="block",
                    event_type="file_copy",
                    classification="secret",
                    channel="removable_media",
                )
            ],
        )

        self.assertEqual(decision.action, "block")
        self.assertEqual(decision.matched_rule_id, "XIG-DLP-USB-SECRET")
        self.assertIn("high_risk", decision.tags)

    def test_high_risk_credential_event_isolates_by_default(self):
        event = EndpointEvent(
            endpoint_id="laptop-002",
            actor="omar",
            event_type="network_upload",
            channel="network_upload",
            resource="browser-password-store",
            classification="credential",
            destination="http://unknown.example/upload",
            severity=35,
            behavior_flags=("new_process", "mass_file_access"),
        )
        decision = evaluate_event(event, [])

        self.assertEqual(decision.action, "isolate_endpoint")
        self.assertGreaterEqual(decision.risk_score, 85)

    def test_low_risk_public_file_is_allowed(self):
        event = EndpointEvent(
            endpoint_id="laptop-003",
            actor="nora",
            event_type="file_open",
            channel="local_file",
            resource="/docs/policy.pdf",
            classification="public",
            severity=5,
        )
        score = calculate_risk_score(event, endpoint_trust=90)
        decision = evaluate_event(event, [], endpoint_trust=90)

        self.assertLess(score, 25)
        self.assertEqual(decision.action, "allow")

    def test_invalid_policy_action_is_rejected(self):
        with self.assertRaises(ValueError):
            PolicyRule(rule_id="bad", name="Bad", action="erase_disk")


if __name__ == "__main__":
    unittest.main()

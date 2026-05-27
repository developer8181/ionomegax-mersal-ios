import unittest

from eipg.core import (
    Action,
    NetworkContext,
    PolicyRule,
    PolicyScope,
    evaluate_access,
    normalize_mac,
    validate_cidr,
    validate_ip,
)


class CorePolicyTests(unittest.TestCase):
    def test_allow_https_from_corporate_subnet(self):
        rules = [
            PolicyRule(
                id=1,
                name="Allow HTTPS",
                action=Action.ALLOW,
                priority=100,
                scope=PolicyScope.GLOBAL,
                source_cidr="10.0.0.0/8",
                destination_ports="443",
                protocols="tcp",
            ),
            PolicyRule(
                id=2,
                name="Default deny",
                action=Action.DENY,
                priority=1,
                scope=PolicyScope.GLOBAL,
            ),
        ]
        ctx = NetworkContext(
            source_ip="10.0.1.50",
            destination_ip="8.8.8.8",
            destination_port=443,
            protocol="tcp",
        )
        decision = evaluate_access(ctx, rules, device_trust_score=60)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.matched_rule_name, "Allow HTTPS")

    def test_deny_when_no_matching_allow(self):
        rules = [
            PolicyRule(
                id=1,
                name="Default deny",
                action=Action.DENY,
                priority=1,
                scope=PolicyScope.GLOBAL,
            ),
        ]
        ctx = NetworkContext(source_ip="192.168.1.1", destination_port=22, protocol="tcp")
        decision = evaluate_access(ctx, rules, device_trust_score=50)
        self.assertFalse(decision.allowed)

    def test_auto_deny_critical_threat(self):
        ctx = NetworkContext(source_ip="10.0.1.1", threat_score=95)
        decision = evaluate_access(ctx, [], device_trust_score=80)
        self.assertFalse(decision.allowed)
        self.assertIn("Critical threat", decision.reason)

    def test_zone_policy_matching(self):
        rules = [
            PolicyRule(
                id=1,
                name="Quarantine guest",
                action=Action.QUARANTINE,
                priority=200,
                scope=PolicyScope.ZONE,
                zones="guest",
            ),
        ]
        ctx = NetworkContext(source_ip="192.168.100.1", zone="guest")
        decision = evaluate_access(ctx, rules, device_trust_score=50)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, Action.QUARANTINE)

    def test_trust_score_gate(self):
        rules = [
            PolicyRule(
                id=1,
                name="Secure only",
                action=Action.ALLOW,
                priority=100,
                scope=PolicyScope.GLOBAL,
                min_trust_score=70,
            ),
        ]
        ctx = NetworkContext(source_ip="10.0.1.1")
        low = evaluate_access(ctx, rules, device_trust_score=30)
        high = evaluate_access(ctx, rules, device_trust_score=80)
        self.assertFalse(low.allowed)
        self.assertTrue(high.allowed)

    def test_ip_validation(self):
        self.assertEqual(validate_ip("10.0.0.1"), "10.0.0.1")
        self.assertEqual(validate_cidr("10.0.0.0/8"), "10.0.0.0/8")

    def test_mac_normalization(self):
        self.assertEqual(normalize_mac("aabbccddeeff"), "aa:bb:cc:dd:ee:ff")
        self.assertEqual(normalize_mac("AA-BB-CC-DD-EE-FF"), "aa:bb:cc:dd:ee:ff")


if __name__ == "__main__":
    unittest.main()

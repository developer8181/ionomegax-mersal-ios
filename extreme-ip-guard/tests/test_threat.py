import unittest

from eipg.crypto import hash_chain, sign_policy_bundle, verify_policy_bundle
from eipg.threat import assess_threat, compute_device_trust, detect_brute_force, detect_port_scan


class ThreatTests(unittest.TestCase):
    def test_port_scan_detection(self):
        event = detect_port_scan(source_ip="1.2.3.4", unique_ports=15, unique_hosts=1)
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, "port_scan")

    def test_brute_force_detection(self):
        event = detect_brute_force(source_ip="1.2.3.4", failed_attempts=10, target_service="ssh")
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, "brute_force")

    def test_assess_threat_auto_block(self):
        events = [
            {"event_type": "port_scan", "severity": 25, "created_at": "2099-01-01T00:00:00+00:00"},
            {"event_type": "brute_force", "severity": 35, "created_at": "2099-01-01T00:00:00+00:00"},
            {"event_type": "brute_force", "severity": 35, "created_at": "2099-01-01T00:00:00+00:00"},
            {"event_type": "brute_force", "severity": 35, "created_at": "2099-01-01T00:00:00+00:00"},
        ]
        assessment = assess_threat(recent_events=events)
        self.assertGreaterEqual(assessment.score, 50)

    def test_device_trust_scoring(self):
        high = compute_device_trust(
            registered=True,
            posture_compliant=True,
            last_seen_hours=0.5,
            violation_count=0,
            attestation_verified=True,
        )
        low = compute_device_trust(
            registered=False,
            posture_compliant=False,
            last_seen_hours=100,
            violation_count=5,
        )
        self.assertGreater(high, low)
        self.assertGreaterEqual(high, 80)


class CryptoTests(unittest.TestCase):
    def test_hash_chain_links_entries(self):
        h1 = hash_chain("genesis", "event1")
        h2 = hash_chain(h1, "event2")
        self.assertNotEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_policy_bundle_signing(self):
        payload = {"version": 1, "rules": [{"name": "test", "action": "deny"}]}
        sig = sign_policy_bundle(payload, "secret-key")
        self.assertTrue(verify_policy_bundle(payload, sig, "secret-key"))
        self.assertFalse(verify_policy_bundle(payload, sig, "wrong-key"))


if __name__ == "__main__":
    unittest.main()

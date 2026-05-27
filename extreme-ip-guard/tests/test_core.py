import unittest

from xipg.core import GuardPolicy, NetworkEvent, normalize_ip, score_event


DEFAULT_POLICY = GuardPolicy(
    name="default",
    mode="enforce",
    trusted_networks=("10.0.0.0/8", "192.168.0.0/16"),
    block_ports=(23, 445, 3389),
    hard_block_countries=("KP", "IR"),
    challenge_threshold=45,
    block_threshold=70,
    quarantine_threshold=90,
)


class CoreRulesTests(unittest.TestCase):
    def test_normalizes_ip_addresses(self):
        self.assertEqual(normalize_ip(" 2001:0db8::0001 "), "2001:db8::1")

    def test_high_risk_event_triggers_quarantine(self):
        decision = score_event(
            NetworkEvent(
                source_ip="10.10.20.17",
                destination_ip="203.0.113.44",
                destination_port=445,
                protocol="tcp",
                country="RU",
                bytes_out=60_000_000,
                bytes_in=500_000,
                process_name="powershell.exe",
                ip_reputation_score=96,
                tor_exit_node=True,
                geo_anomaly=True,
                burst_connections=800,
                asset_criticality="critical",
            ),
            DEFAULT_POLICY,
        )

        self.assertEqual(decision.action, "quarantine")
        self.assertEqual(decision.severity, "critical")
        self.assertGreaterEqual(decision.risk_score, 90)

    def test_trusted_private_traffic_is_allowed(self):
        decision = score_event(
            NetworkEvent(
                source_ip="10.10.20.17",
                destination_ip="10.2.3.4",
                destination_port=443,
                protocol="tcp",
                country="SA",
                bytes_out=5_000,
                bytes_in=30_000,
                process_name="chrome.exe",
                ip_reputation_score=5,
                tor_exit_node=False,
                geo_anomaly=False,
                burst_connections=2,
                asset_criticality="medium",
            ),
            DEFAULT_POLICY,
        )

        self.assertEqual(decision.action, "allow")
        self.assertEqual(decision.severity, "info")

    def test_hard_block_country_forces_quarantine(self):
        decision = score_event(
            NetworkEvent(
                source_ip="10.10.20.17",
                destination_ip="198.51.100.5",
                destination_port=443,
                protocol="tcp",
                country="IR",
                bytes_out=2_000,
                bytes_in=1_500,
                process_name="curl",
                ip_reputation_score=10,
                tor_exit_node=False,
                geo_anomaly=False,
                burst_connections=1,
                asset_criticality="medium",
            ),
            DEFAULT_POLICY,
        )

        self.assertEqual(decision.action, "quarantine")


if __name__ == "__main__":
    unittest.main()

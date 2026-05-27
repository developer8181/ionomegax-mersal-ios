import unittest

from xipg.agents import build_heartbeat, normalize_control_profile, supported_control_profiles


class AgentMetadataTests(unittest.TestCase):
    def test_normalizes_control_profiles(self):
        self.assertEqual(normalize_control_profile("Windows WFP"), "windows-wfp")
        self.assertEqual(normalize_control_profile("unknown profile"), "generic-gateway")

    def test_supported_profiles_include_major_platforms(self):
        profiles = {profile["id"] for profile in supported_control_profiles()}

        self.assertIn("linux-ebpf", profiles)
        self.assertIn("windows-wfp", profiles)
        self.assertIn("mac-network-extension", profiles)
        self.assertIn("generic-gateway", profiles)

    def test_build_heartbeat_rejects_unknown_agent_type(self):
        with self.assertRaises(ValueError):
            build_heartbeat(agent_id="sensor-1", agent_type="unknown")

    def test_build_heartbeat_payload_normalizes_metadata(self):
        heartbeat = build_heartbeat(
            agent_id="sensor-1",
            agent_type="sensor",
            metadata={"control_profile": "Windows WFP", "segment": "finance"},
        )

        self.assertEqual(heartbeat.agent_id, "sensor-1")
        self.assertEqual(heartbeat.agent_type, "sensor")
        self.assertEqual(heartbeat.metadata["control_profile"], "windows-wfp")


if __name__ == "__main__":
    unittest.main()

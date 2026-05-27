import unittest

from epms.agents import build_heartbeat, normalize_vendor, platform_profile, supported_platforms


class AgentMetadataTests(unittest.TestCase):
    def test_normalizes_vendor_names(self):
        self.assertEqual(normalize_vendor("Konica Minolta"), "konica-minolta")
        self.assertEqual(normalize_vendor("unknown brand"), "generic")

    def test_platform_profile_includes_fallback_for_generic_printers(self):
        profile = platform_profile("unknown")

        self.assertEqual(profile["vendor"], "generic")
        self.assertFalse(profile["embedded"])
        self.assertIn("release_station", profile["capabilities"])

    def test_supported_platforms_include_major_embedded_vendors(self):
        vendors = {profile["vendor"] for profile in supported_platforms()}

        self.assertIn("hp", vendors)
        self.assertIn("canon", vendors)
        self.assertIn("ricoh", vendors)
        self.assertIn("xerox", vendors)
        self.assertIn("generic", vendors)

    def test_build_heartbeat_rejects_unknown_agent_type(self):
        with self.assertRaises(ValueError):
            build_heartbeat(agent_id="agent-1", agent_type="unknown")

    def test_build_heartbeat_payload(self):
        heartbeat = build_heartbeat(
            agent_id="client-1",
            agent_type="client",
            metadata={"direct_print_monitor": True},
        )

        self.assertEqual(heartbeat.agent_id, "client-1")
        self.assertEqual(heartbeat.agent_type, "client")
        self.assertTrue(heartbeat.metadata["direct_print_monitor"])


if __name__ == "__main__":
    unittest.main()

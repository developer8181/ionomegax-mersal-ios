import unittest

from eipg.agents import SUPPORTED_AGENT_TYPES, build_heartbeat, supported_backends


class AgentTests(unittest.TestCase):
    def test_build_heartbeat(self):
        hb = build_heartbeat(agent_id="edge-01", agent_type="edge-enforcer", metadata={"backend": "nftables"})
        self.assertEqual(hb.agent_type, "edge-enforcer")
        self.assertEqual(hb.metadata["backend"], "nftables")
        self.assertTrue(hb.hostname)

    def test_rejects_invalid_agent_type(self):
        with self.assertRaises(ValueError):
            build_heartbeat(agent_id="x", agent_type="invalid")

    def test_supported_backends(self):
        backends = supported_backends()
        ids = {b["id"] for b in backends}
        self.assertIn("nftables", ids)
        self.assertIn("ebpf-xdp", ids)

    def test_agent_types_include_nac(self):
        self.assertIn("nac-gateway", SUPPORTED_AGENT_TYPES)
        self.assertIn("flow-collector", SUPPORTED_AGENT_TYPES)


if __name__ == "__main__":
    unittest.main()

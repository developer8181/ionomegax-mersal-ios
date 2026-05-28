import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.policy_mesh import HolonIdentity, PolicyBundle, merge_bundles, trust_adjustment


class PolicyMeshTests(unittest.TestCase):
    def test_merge_remote_newer(self):
        local = PolicyBundle("b1", 1, [{"rule_id": "A"}])
        remote = PolicyBundle("b1", 2, [{"rule_id": "B"}])
        merged = merge_bundles(local, remote)
        self.assertEqual(merged.version, 2)
        self.assertEqual(len(merged.rules), 2)

    def test_trust_adjustment_bounds(self):
        holon = HolonIdentity("h1", "endpoint", "HQ", trust_score=50)
        self.assertGreaterEqual(trust_adjustment(holon, 90), 0)
        self.assertLessEqual(trust_adjustment(holon, 10), 100)


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from xig.enforcement import LocalEnforcer


class EnforcementTests(unittest.TestCase):
    def test_block_and_isolate_persist_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            enforcer = LocalEnforcer(Path(tmp))
            enforcer.apply("block", reason="secret usb", channel="removable_media")
            state = enforcer.load()
            self.assertIn("removable_media", state.blocked_channels)
            enforcer.apply("isolate_endpoint", reason="credential leak")
            state = enforcer.load()
            self.assertTrue(state.isolated)
            enforcer.restore()
            self.assertFalse(enforcer.load().isolated)


if __name__ == "__main__":
    unittest.main()

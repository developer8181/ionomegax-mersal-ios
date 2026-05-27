import tempfile
import unittest
from pathlib import Path

from xig.storage import Database


class DirectivesTests(unittest.TestCase):
    def test_endpoint_directives_include_policies(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "test.sqlite3")
            db.init_schema()
            db.seed_demo()
            payload = db.endpoint_directives("endpoint-demo-001")
            self.assertEqual(payload["endpoint_id"], "endpoint-demo-001")
            self.assertGreater(payload["policy_count"], 0)
            self.assertIn("isolate_endpoint", payload["actions"])


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from pathlib import Path

from epms.health import health_report
from epms.storage import Database


class HealthTests(unittest.TestCase):
    def test_health_report_healthy(self):
        with tempfile.TemporaryDirectory() as tempdir:
            db = Database(Path(tempdir) / "epms.sqlite3")
            db.init_schema()
            db.seed_demo()
            report = health_report(db, settings_summary={"require_auth": False})
            self.assertEqual(report["status"], "healthy")
            self.assertTrue(report["database"])


if __name__ == "__main__":
    unittest.main()

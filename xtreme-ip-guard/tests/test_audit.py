# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
import tempfile
import unittest
from pathlib import Path

from xig.storage import Database


class AuditTests(unittest.TestCase):
    def test_record_and_list_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Database(Path(tmp) / "test.sqlite3")
            db.init_schema()
            entry = db.record_audit("admin", "endpoint.isolate", target="laptop-001")
            rows = db.list_audit()
            self.assertEqual(rows[0]["audit_id"], entry["audit_id"])
            self.assertEqual(rows[0]["action"], "endpoint.isolate")


if __name__ == "__main__":
    unittest.main()

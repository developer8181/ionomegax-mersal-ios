# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

from __future__ import annotations

import json
import os
import tempfile
import unittest
from http.client import HTTPConnection
from threading import Thread
from unittest import mock

from xig.server import run


class EnterpriseSecurityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "ent.sqlite3")
        self.env = {
            "MERSAL_DB": self.db_path,
            "MERSAL_PRODUCTION": "1",
            "MERSAL_ENTERPRISE": "1",
            "MERSAL_BOOTSTRAP": "0",
            "MERSAL_NO_SCHEDULER": "1",
            "MERSAL_SIGNING_SECRET": "x" * 48,
            "MERSAL_API_TOKEN": "enterprise-test-token-32chars-minimum-len",
            "MERSAL_ADMIN_PASSWORD": "AdminPass123!",
            "MERSAL_PORT": "28191",
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _start_server(self) -> None:
        self.server_thread = Thread(target=run, daemon=True)
        self.server_thread.start()

    def test_viewer_cannot_create_policy(self) -> None:
        with mock.patch.dict(os.environ, self.env, clear=False):
            from xig.storage import Database
            from xig.rbac import RbacEngine

            db = Database(self.db_path)
            db.init_schema()
            db.ensure_rbac_seed()
            rbac = RbacEngine(db)
            with db.connect() as conn:
                conn.execute(
                    """
                    INSERT INTO rbac_users (user_id, tenant_id, username, password_hash, role, display_name)
                    VALUES ('u-viewer', 'default', 'viewer1', ?, 'viewer', 'Viewer')
                    """,
                    (rbac.hash_password("ViewerPass1!"),),
                )

            self._start_server()
            import time

            for _ in range(30):
                try:
                    c = HTTPConnection("127.0.0.1", 28191, timeout=2)
                    c.request("GET", "/api/system/about")
                    if c.getresponse().status == 200:
                        break
                except OSError:
                    pass
                time.sleep(0.2)

            from xig.auth import create_session_token

            token = create_session_token("viewer1", role="viewer", tenant_id="default")
            c = HTTPConnection("127.0.0.1", 28191, timeout=5)
            body = json.dumps(
                {
                    "rule_id": "TEST-RULE",
                    "name": "blocked",
                    "action": "block",
                }
            )
            c.request(
                "POST",
                "/api/policies",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Mersal-Token": token,
                },
            )
            resp = c.getresponse()
            self.assertEqual(resp.status, 403)

    def test_audit_chain_valid_after_actions(self) -> None:
        with mock.patch.dict(os.environ, self.env, clear=False):
            from xig.storage import Database

            db = Database(self.db_path)
            db.init_schema()
            db.record_audit("admin", "test.action", target="t1", tenant_id="default")
            db.record_audit("admin", "test.action2", target="t2", tenant_id="default")
            report = db.verify_audit_chain()
            self.assertTrue(report["valid"])
            self.assertGreaterEqual(report["records_checked"], 2)


if __name__ == "__main__":
    unittest.main()

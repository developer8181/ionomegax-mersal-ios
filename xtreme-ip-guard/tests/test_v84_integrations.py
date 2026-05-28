# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import tempfile
import unittest
from unittest.mock import patch

from xig.db.sql_dialect import adapt_sql, events_window_count_sql
from xig.integrations.integration_hub import IntegrationHub
from xig.integrations.scim import ScimProvisioner
from xig.integrations.siem_forwarder import SiemForwarder
from xig.storage import Database
from xig.xdr.soar_bridge import XdrSoarBridge


class V84IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(self.tmp.name + "/test.sqlite3")
        self.db.init_schema()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_adapt_sql_insert_or_ignore_sqlite(self) -> None:
        with patch.dict(os.environ, {"MERSAL_POSTGRES_DSN": ""}, clear=False):
            sql = "INSERT OR IGNORE INTO policies (policy_id) VALUES (?)"
            self.assertIn("INSERT OR IGNORE", adapt_sql(sql))

    def test_events_window_sqlite(self) -> None:
        with patch.dict(os.environ, {"MERSAL_POSTGRES_DSN": ""}, clear=False):
            query, params = events_window_count_sql(endpoint_id="ep-1", window_seconds=60)
            self.assertIn("datetime('now'", query)
            self.assertEqual(params[0], "ep-1")

    def test_integration_hub_matrix(self) -> None:
        hub = IntegrationHub(self.db).full_matrix()
        self.assertIn("identity", hub)
        self.assertIn("autonomous_cycle", hub["operations"]["scheduler_jobs"])

    def test_siem_forward_cursor(self) -> None:
        result = SiemForwarder(self.db).forward_batch()
        self.assertTrue(result.get("skipped") or "cursor" in result)

    def test_scim_patch_delete(self) -> None:
        from xig.rbac import RbacEngine

        rbac = RbacEngine(self.db)
        user = self.db.create_rbac_user(
            username="scim-user",
            password_hash=rbac.hash_password("Mersal-Test-Password-99!"),
            role="analyst",
        )
        prov = ScimProvisioner(self.db)
        updated = prov.patch_user(user["user_id"], {"active": False, "roles": [{"value": "viewer"}]})
        self.assertIsNotNone(updated)
        self.assertFalse(updated["active"])
        self.assertTrue(prov.delete_user(user["user_id"]))

    def test_xdr_soar_bridge_empty(self) -> None:
        from xig.soar import SoarEngine

        result = XdrSoarBridge(self.db, SoarEngine(self.db)).execute_for_findings()
        self.assertIn("executed", result)


if __name__ == "__main__":
    unittest.main()

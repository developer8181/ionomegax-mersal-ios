# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import tempfile
import unittest

from xig.integrations.oidc import OidcProvider
from xig.integrations.siem_forwarder import SiemForwarder
from xig.platform_ops.health import PlatformHealth
from xig.platform_ops.backup import BackupManager
from xig.storage import Database


class StandaloneV8Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmp.name, "v8.sqlite3"))
        self.db.init_schema()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_platform_health(self) -> None:
        status = PlatformHealth(self.db).full_status()
        self.assertIn("modules", status)
        self.assertIn("readiness", status)

    def test_siem_forwarder_skip_without_config(self) -> None:
        result = SiemForwarder(self.db).forward_batch()
        self.assertTrue(result.get("skipped"))

    def test_backup_roundtrip(self) -> None:
        self.db.record_audit("test", "init")
        meta = BackupManager(self.db).create_backup(dest_dir=self.tmp.name)
        self.assertTrue(meta.get("backup_id"))
        self.assertGreater(meta.get("size_bytes", 0), 0)

    def test_oidc_not_configured(self) -> None:
        self.assertFalse(OidcProvider(self.db).configured())


if __name__ == "__main__":
    unittest.main()

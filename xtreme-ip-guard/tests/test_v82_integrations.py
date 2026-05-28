# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import tempfile
import unittest

from xig.db.adapter import adapt_ddl_for_postgres, uses_postgres
from xig.edr.ebpf_probe import collect_ebpf_snapshot, ebpf_available
from xig.integrations.saml import SamlProvider
from xig.integrations.scim import ScimProvisioner
from xig.platform_ops.updates import UpdateChannel
from xig.storage import Database


class V82IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmp.name, "v82.sqlite3"))
        self.db.init_schema()
        os.environ["MERSAL_UPDATE_SIGNING_KEY"] = "test-update-signing-key-32bytes"

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("MERSAL_UPDATE_SIGNING_KEY", None)

    def test_ddl_adapt_autoincrement(self) -> None:
        ddl = "id INTEGER PRIMARY KEY AUTOINCREMENT"
        self.assertIn("SERIAL", adapt_ddl_for_postgres(ddl))

    def test_signed_update_manifest(self) -> None:
        ch = UpdateChannel(self.db)
        meta = ch.publish_manifest(
            component="agent",
            version="8.2.0",
            artifact_url="https://cdn.example/mersal-agent.tar.gz",
            checksum_sha256="abc123",
        )
        latest = ch.latest_for("agent")
        self.assertIsNotNone(latest)
        self.assertTrue(ch.verify_manifest(latest))

    def test_scim_env_token(self) -> None:
        os.environ["MERSAL_SCIM_TOKEN"] = "scim-secret-token"
        self.assertTrue(ScimProvisioner(self.db).verify_bearer("scim-secret-token"))
        os.environ.pop("MERSAL_SCIM_TOKEN")

    def test_saml_not_configured(self) -> None:
        self.assertFalse(SamlProvider(self.db).configured())

    def test_ebpf_probe(self) -> None:
        snap = collect_ebpf_snapshot()
        self.assertIn("available", snap)
        self.assertIsInstance(ebpf_available(), bool)

    def test_postgres_flag_default(self) -> None:
        os.environ.pop("MERSAL_POSTGRES_DSN", None)
        self.assertFalse(uses_postgres())


if __name__ == "__main__":
    unittest.main()

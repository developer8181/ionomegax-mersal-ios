import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from epms.config import Settings
from epms.device_servlet import handle_get, handle_post
from epms.production import production_checklist, validate_production_settings
from epms.storage import Database


class ProductionReadyTests(unittest.TestCase):
    def test_production_validation_rejects_weak_secrets(self):
        settings = Settings(
            db_path=Path("/tmp/x.sqlite3"),
            pg_dsn=None,
            agent_token="replace-with-agent-token",
            session_secret="change-me-in-production",
            require_auth=False,
            anonymize_documents=True,
            audit_retention_days=365,
            tls_cert=None,
            tls_key=None,
            site_id="hq",
            upstream_url="http://127.0.0.1:8080",
            host="0.0.0.0",
            port=8080,
            bootstrap_admin_password=None,
            production_mode=True,
            seed_demo=False,
        )
        errors, _ = validate_production_settings(settings)
        self.assertGreater(len(errors), 0)

    def test_device_servlet_health_and_auth(self):
        with tempfile.TemporaryDirectory() as tempdir:
            db = Database(Path(tempdir) / "t.sqlite3")
            db.init_schema()
            db.seed_demo()
            health = handle_get("/extreme/sdk/v1/health", db)
            self.assertTrue(health["ok"])
            auth = handle_post(
                "/extreme/sdk/v1/auth",
                db,
                {"username": "ahmed"},
                anonymize=False,
            )
            self.assertEqual(auth["username"], "ahmed")
            self.assertTrue(auth["session_token"])

    def test_production_checklist_ready_with_valid_env(self):
        settings = Settings(
            db_path=Path("/tmp/x.sqlite3"),
            pg_dsn=None,
            agent_token="a" * 40,
            session_secret="b" * 40,
            require_auth=True,
            anonymize_documents=True,
            audit_retention_days=365,
            tls_cert=None,
            tls_key=None,
            site_id="hq",
            upstream_url="http://127.0.0.1:8080",
            host="0.0.0.0",
            port=8080,
            bootstrap_admin_password="StrongPass123!",
            production_mode=True,
            seed_demo=False,
        )
        report = production_checklist(database_ok=True, settings=settings)
        self.assertTrue(report["ready"])


if __name__ == "__main__":
    unittest.main()

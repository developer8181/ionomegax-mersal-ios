# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from xig.agent.event_queue import AgentEventQueue
from xig.integrations.federation_roles import resolve_role_from_claims
from xig.integrations.integration_hub import IntegrationHub
from xig.integrations.saml_verify import verify_saml_response
from xig.platform_ops.backup import BackupManager
from xig.security.access import enterprise_startup_errors
from xig.storage import Database


class V85EnterpriseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(self.tmp.name + "/ent.sqlite3")
        self.db.init_schema()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_federation_role_mapping(self) -> None:
        with patch.dict(
            os.environ,
            {"MERSAL_GROUP_ROLE_MAP": '{"SOC-Admins": "soc_admin", "Auditors": "viewer"}'},
            clear=False,
        ):
            role = resolve_role_from_claims({"groups": ["SOC-Admins"]}, default_role="analyst")
            self.assertEqual(role, "soc_admin")

    def test_agent_event_queue(self) -> None:
        from pathlib import Path

        q = AgentEventQueue(Path(self.tmp.name) / "agent-state")
        item_id = q.enqueue({"endpoint_id": "ep-1", "event_type": "test"})
        self.assertEqual(q.depth(), 1)
        pending = q.pending()
        self.assertEqual(pending[0][0], item_id)
        q.ack(item_id)
        self.assertEqual(q.depth(), 0)

    def test_backup_sqlite(self) -> None:
        meta = BackupManager(self.db).create_backup()
        self.assertTrue(meta.get("backup_id"))
        health = BackupManager(self.db).health()
        self.assertGreaterEqual(health["count"], 1)

    def test_integration_hub_enterprise_tier(self) -> None:
        hub = IntegrationHub(self.db).full_matrix()
        self.assertEqual(hub["tier"], "enterprise-reliability")
        self.assertIn("backup", hub["data_plane"])

    def test_enterprise_strict_startup_requires_tls(self) -> None:
        env = {
            "MERSAL_ENTERPRISE": "1",
            "MERSAL_PRODUCTION": "1",
            "MERSAL_ENTERPRISE_STRICT": "1",
        }
        with patch.dict(os.environ, env, clear=False):
            errors = enterprise_startup_errors()
            self.assertTrue(any("TLS" in e for e in errors))

    def test_saml_conditions_reject_expired(self) -> None:
        xml = b"""<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
            xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
            <saml:Assertion>
            <saml:Conditions NotOnOrAfter="2000-01-01T00:00:00Z"/>
            <saml:Subject><saml:NameID>user@bank.gov</saml:NameID></saml:Subject>
            </saml:Assertion></samlp:Response>"""
        with patch.dict(os.environ, {"MERSAL_SAML_STRICT": "0"}, clear=False):
            ok, err, _ = verify_saml_response(xml, sp_entity_id="mersal-sp")
            self.assertFalse(ok)
            self.assertIn("Conditions", err)


if __name__ == "__main__":
    unittest.main()

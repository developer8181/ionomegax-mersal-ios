import tempfile
import unittest
from pathlib import Path

from eig.storage import Database


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(Path(self.tmp.name) / "test.sqlite3")
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_ingest_creates_incident_on_block(self) -> None:
        result = self.db.ingest_event(
            {
                "hostname": "ws-finance-01",
                "category": "network",
                "summary": "Unauthorized connect from external host",
                "detail": "blocked unauthorized access attempt",
            }
        )
        self.assertEqual(result["decision"]["action"], "block")
        incidents = self.db.list_incidents()
        self.assertGreaterEqual(len(incidents), 1)

    def test_agent_registration(self) -> None:
        self.db.register_agent(
            {
                "agent_id": "test-agent-1",
                "agent_type": "endpoint",
                "hostname": "ws-dev-14",
                "version": "0.1.0",
                "trust_score": 80,
            }
        )
        agents = self.db.list_agents()
        self.assertEqual(len(agents), 1)


if __name__ == "__main__":
    unittest.main()

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from epms.embedded import get_adapter
from epms.embedded.hp import HPAdapter
from epms.storage import Database


class EmbeddedAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "epms.sqlite3"
        self.db = Database(self.db_path)
        self.db.init_schema()
        self.db.seed_demo()

    def tearDown(self):
        self.tempdir.cleanup()

    def _users_payload(self):
        return self.db.list_users()

    def test_hp_adapter_capabilities(self):
        adapter = HPAdapter(server_url="http://127.0.0.1:8080", device_address="https://mfd.example/oxp")
        caps = adapter.device_capabilities()
        self.assertEqual(caps["vendor"], "hp")
        self.assertIn("release", caps["capabilities"])

    def test_gateway_authenticate_and_list_held(self):
        adapter = get_adapter(vendor="generic", server_url="http://127.0.0.1:8080")
        users = self._users_payload()
        username = users[0]["username"]
        with patch.object(adapter, "_request", side_effect=lambda path, **kwargs: self._mock_request(path, **kwargs)):
            session = adapter.authenticate(username=username)
            self.assertEqual(session.username, username)
            held = adapter.list_held_jobs(username=username)
            self.assertIsInstance(held, list)

    def _mock_request(self, path: str, *, method: str = "GET", payload=None):
        if path == "/api/users":
            return self.db.list_users()
        if path.startswith("/api/release/held/"):
            username = path.rsplit("/", 1)[-1]
            return self.db.list_held_jobs_for_user(username=username)
        if method == "POST" and "/release" in path:
            return {"status": "printed"}
        raise AssertionError(f"unexpected path {path}")


if __name__ == "__main__":
    unittest.main()

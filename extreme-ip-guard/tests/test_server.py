import json
import os
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from xig.server import _Handler
from xig.storage import Database


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3")
        cls.tmp.close()
        os.unlink(cls.tmp.name)
        cls.db = Database(cls.tmp.name)
        cls.db.init_schema()
        cls.db.seed_demo()

        cls.port = _free_port()

        def factory(*args, **kwargs):
            return _Handler(*args, database=cls.db, **kwargs)

        os.environ["XIG_QUIET"] = "1"
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", cls.port), factory)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        try:
            os.unlink(cls.tmp.name)
        except FileNotFoundError:
            pass

    def _post(self, path, payload):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get(self, path):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def test_dashboard_returns_totals(self):
        body = self._get("/api/dashboard")
        self.assertIn("totals", body)
        self.assertIn("agents", body["totals"])

    def test_enrol_flow_and_event_ingest(self):
        token = self._post("/api/agents/enrol-tokens", {"hostname": "WS-INT-01"})["enrol_token"]
        self._post(
            "/api/agents/enrol",
            {
                "enrol_token": token,
                "agent_id": "agent-int-01",
                "hw_fp": "hw",
                "os_name": "Test OS",
                "version": "0.1.0",
            },
        )
        body = self._post(
            "/api/events",
            {
                "agent_id": "agent-int-01",
                "kind": "file.write",
                "subject": "usb",
                "data": {"path": "/media/usb/x.zip", "bytes": 80_000_000},
            },
        )
        self.assertTrue(body["alerts"])
        pending = self._get("/api/agents/poll?agent_id=agent-int-01")
        self.assertTrue(pending)

    def test_invalid_event_kind_rejected(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._post(
                "/api/events",
                {"agent_id": "agent-int-01", "kind": "not-real", "data": {}},
            )
        self.assertEqual(ctx.exception.code, 400)


if __name__ == "__main__":
    unittest.main()

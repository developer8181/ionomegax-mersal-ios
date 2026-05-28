# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

import json
import os
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path


class IntegrationHttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.tmpdir.name) / "integration.sqlite3"
        os.environ["MERSAL_DB"] = str(cls.db_path)
        os.environ["MERSAL_PRODUCTION"] = "1"
        os.environ["MERSAL_API_TOKEN"] = "integration-test-token-32chars-minimum"
        os.environ["MERSAL_SIGNING_SECRET"] = "x" * 48
        os.environ["MERSAL_BOOTSTRAP"] = "0"
        os.environ["MERSAL_PORT"] = "28190"
        os.environ["MERSAL_HOST"] = "127.0.0.1"
        os.environ["MERSAL_NO_SCHEDULER"] = "1"
        os.environ["MERSAL_KEV_FEED_URL"] = ""

        from xig.server import run

        cls.server_thread = threading.Thread(
            target=lambda: run(host="127.0.0.1", port=28190),
            name="integration-server",
            daemon=True,
        )
        cls.server_thread.start()
        cls.base = "http://127.0.0.1:28190"
        for _ in range(40):
            try:
                with urllib.request.urlopen(f"{cls.base}/api/system/about", timeout=1) as resp:
                    if resp.status == 200:
                        break
            except OSError:
                time.sleep(0.25)

    @classmethod
    def tearDownClass(cls):
        cls.tmpdir.cleanup()

    def _get(self, path: str, token: str = ""):
        headers = {"X-Mersal-Token": token} if token else {}
        request = urllib.request.Request(f"{self.base}{path}", headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode())

    def _post(self, path: str, body: dict, token: str = ""):
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Mersal-Token"] = token
        request = urllib.request.Request(
            f"{self.base}{path}", data=data, headers=headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode())

    def test_public_about_and_build(self):
        about = self._get("/api/system/about")
        self.assertEqual(about["version"], "8.8.0")
        build = self._get("/api/system/build")
        self.assertEqual(build["version"], "8.8.0")
        self.assertIn("components", build)

    def test_readiness_without_auth(self):
        report = self._get("/api/system/readiness")
        self.assertIn("checks", report)
        self.assertTrue(report["production_mode"])

    def test_authorized_dashboard_and_threat_intel(self):
        token = os.environ["MERSAL_API_TOKEN"]
        dash = self._get("/api/dashboard", token=token)
        self.assertIn("totals", dash)
        threat = self._get("/api/threat/intel", token=token)
        self.assertIn("total_indicators", threat)

    def test_enterprise_dashboard(self):
        token = os.environ["MERSAL_API_TOKEN"]
        dash = self._get("/api/enterprise/dashboard", token=token)
        self.assertEqual(dash["suite"], "Mersal Enterprise Security Suite")
        matrix = self._get("/api/enterprise/matrix", token=token)
        self.assertGreaterEqual(len(matrix), 3)

    def test_agent_heartbeat_and_event(self):
        token = os.environ["MERSAL_API_TOKEN"]
        self._post(
            "/api/agents/heartbeat",
            {
                "agent_id": "int-agent-1",
                "hostname": "int-host",
                "os_name": "Linux",
                "metadata": {
                    "endpoint_id": "int-host",
                    "vuln_probe": {"open_ports": [22, 445]},
                    "security_features": {"disk_encryption": False},
                },
            },
            token=token,
        )
        result = self._post(
            "/api/events",
            {
                "endpoint_id": "int-host",
                "actor": "tester",
                "event_type": "file_copy",
                "channel": "removable_media",
                "resource": "/tmp/secret.doc",
                "classification": "secret",
            },
            token=token,
        )
        self.assertIn("action", result)


if __name__ == "__main__":
    unittest.main()

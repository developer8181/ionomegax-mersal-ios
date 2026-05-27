import unittest
from unittest.mock import patch

from epms.embedded.sdk_clients.registry import get_device_client, list_device_clients
from epms.embedded.sdk_clients.vendor_impl import build_kyocera_client, build_ricoh_client


class SdkClientTests(unittest.TestCase):
    def test_list_all_vendor_clients(self):
        clients = list_device_clients()
        vendors = {row["vendor"] for row in clients}
        self.assertTrue(
            {
                "hp",
                "canon",
                "ricoh",
                "xerox",
                "konica-minolta",
                "kyocera",
                "lexmark",
                "olivetti",
            }.issubset(vendors)
        )

    @patch("epms.embedded.sdk_clients.extreme_gateway.post_json")
    def test_handshake_uses_extreme_servlet_first(self, mock_post):
        mock_post.return_value = {"ok": True, "product": "Extreme Print"}
        client = build_ricoh_client("https://mfd.example")
        result = client.handshake()
        self.assertEqual(result["mode"], "extreme-servlet")
        self.assertIn("extreme/sdk/v1/health", mock_post.call_args[0][0])

    @patch("epms.embedded.sdk_clients.extreme_gateway.post_json")
    def test_authenticate_returns_session_token(self, mock_post):
        mock_post.return_value = {"ok": True, "username": "finance", "session_token": "ricoh-finance"}
        client = get_device_client("ricoh", "https://mfd.example")
        auth = client.authenticate(username="finance", pin="1234")
        self.assertTrue(auth.ok)
        self.assertEqual(auth.session_token, "ricoh-finance")

    @patch("epms.embedded.sdk_clients.vendor_impl.post_json")
    @patch("epms.embedded.sdk_clients.extreme_gateway.post_json")
    def test_release_job_falls_back_to_native(self, mock_extreme, mock_native):
        mock_extreme.side_effect = RuntimeError("extreme servlet unavailable")
        mock_native.return_value = {"ok": True, "message": "released"}
        client = build_kyocera_client("https://mfd.example")
        action = client.release_job(9, username="finance", session_token="tok")
        self.assertTrue(action.ok)
        self.assertIn("hypas", mock_native.call_args[0][0])


if __name__ == "__main__":
    unittest.main()

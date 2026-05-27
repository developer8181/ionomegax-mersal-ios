import os
import unittest

from epms.embedded import get_adapter
from epms.embedded.kyocera import KyoceraHyPASAdapter
from epms.embedded.konica import KonicaMinoltaOpenAPIAdapter
from epms.embedded.lexmark import LexmarkESFAdapter
from epms.embedded.olivetti import OlivettiConnectAdapter
from epms.embedded.ricoh import RicohSmartSDKAdapter
from epms.embedded.sdk_registry import is_sdk_active, list_active_sdks
from epms.embedded.xerox import XeroxEIPAdapter


class SdkVendorTests(unittest.TestCase):
    def test_requested_vendors_are_active_by_default(self):
        for vendor in ("kyocera", "olivetti", "xerox", "lexmark", "ricoh", "konica-minolta"):
            self.assertTrue(is_sdk_active(vendor), vendor)

    def test_adapter_types(self):
        cases = {
            "kyocera": KyoceraHyPASAdapter,
            "olivetti": OlivettiConnectAdapter,
            "xerox": XeroxEIPAdapter,
            "lexmark": LexmarkESFAdapter,
            "ricoh": RicohSmartSDKAdapter,
            "konica-minolta": KonicaMinoltaOpenAPIAdapter,
        }
        for vendor, expected_cls in cases.items():
            adapter = get_adapter(vendor=vendor, server_url="http://127.0.0.1:8080")
            self.assertIsInstance(adapter, expected_cls)

    def test_sdk_capabilities_report_active(self):
        adapter = get_adapter(
            vendor="ricoh",
            server_url="http://127.0.0.1:8080",
            device_address="https://mfd.example/ricoh",
        )
        caps = adapter.device_capabilities()
        self.assertEqual(caps["sdk"]["status"], "active")
        self.assertEqual(caps["sdk"]["integration"], "http-native")
        self.assertEqual(caps["device_protocol"], "ricoh-smartsdk-http")
        self.assertEqual(caps["sdk_module"], "epms.embedded.ricoh")

    def test_list_active_sdks_includes_all_vendors(self):
        vendors = {row["vendor"] for row in list_active_sdks()}
        self.assertTrue({"kyocera", "olivetti", "xerox", "lexmark", "ricoh", "konica-minolta"}.issubset(vendors))

    def test_disable_single_vendor_via_env(self):
        old = os.environ.get("EPMS_SDK_OLIVETTI")
        os.environ["EPMS_SDK_OLIVETTI"] = "disable"
        try:
            self.assertFalse(is_sdk_active("olivetti"))
            adapter = get_adapter(vendor="olivetti", server_url="http://127.0.0.1:8080")
            with self.assertRaises(RuntimeError):
                adapter.authenticate(username="demo")
        finally:
            if old is None:
                os.environ.pop("EPMS_SDK_OLIVETTI", None)
            else:
                os.environ["EPMS_SDK_OLIVETTI"] = old


if __name__ == "__main__":
    unittest.main()

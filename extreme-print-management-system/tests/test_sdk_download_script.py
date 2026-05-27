import json
import unittest
from pathlib import Path


class SdkDownloadScriptTests(unittest.TestCase):
    def test_portals_file_lists_all_vendors(self):
        portals_path = Path(__file__).resolve().parents[1] / "scripts" / "vendor_sdk_portals.json"
        portals = json.loads(portals_path.read_text(encoding="utf-8"))
        expected = {
            "hp",
            "canon",
            "ricoh",
            "xerox",
            "konica-minolta",
            "kyocera",
            "lexmark",
            "olivetti",
        }
        self.assertTrue(expected.issubset(set(portals.keys())))

    def test_download_script_exists(self):
        script = Path(__file__).resolve().parents[1] / "scripts" / "download_vendor_sdks.py"
        self.assertTrue(script.exists())


if __name__ == "__main__":
    unittest.main()

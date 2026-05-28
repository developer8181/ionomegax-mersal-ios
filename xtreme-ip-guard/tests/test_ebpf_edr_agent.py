# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import unittest

from xig.edr.ebpf_edr import build_ebpf_edr_detections, collect_agent_ebpf_edr
from xig.edr.libbpf_loader import collect_libbpf_status, libbpf_available


class EbpfEdrAgentTests(unittest.TestCase):
    def test_build_detections_suspicious_name(self) -> None:
        programs = [{"name": "hide_rootkit_hook", "type": "kprobe", "uid": 1000}]
        ctx = {"program_count": 1, "map_count": 1}
        dets = build_ebpf_edr_detections(programs, ctx)
        self.assertTrue(any(d["type"] == "ebpf_suspicious_program" for d in dets))

    def test_build_detections_program_storm(self) -> None:
        dets = build_ebpf_edr_detections([], {"program_count": 100, "map_count": 1})
        self.assertTrue(any(d["type"] == "ebpf_program_storm" for d in dets))

    def test_collect_agent_returns_structure(self) -> None:
        result = collect_agent_ebpf_edr(include_detections=False)
        self.assertIn("available", result)

    def test_libbpf_disabled_via_env(self) -> None:
        prev = os.environ.get("MERSAL_LIBBPF")
        os.environ["MERSAL_LIBBPF"] = "0"
        try:
            self.assertFalse(libbpf_available())
            status = collect_libbpf_status()
            self.assertFalse(status["available"])
            self.assertEqual(status["engine"], "libbpf")
        finally:
            if prev is None:
                os.environ.pop("MERSAL_LIBBPF", None)
            else:
                os.environ["MERSAL_LIBBPF"] = prev


if __name__ == "__main__":
    unittest.main()

import unittest

from xig.core import EventKind, TelemetryEvent, utc_now_iso
from xig.detection import DetectionEngine
from xig.policies import default_iocs, default_rules


def make_event(kind, data, agent_id="agent-1"):
    return TelemetryEvent(agent_id=agent_id, kind=kind.value, ts=utc_now_iso(), subject="t", data=data)


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.engine = DetectionEngine(rules=default_rules(), iocs=default_iocs())

    def test_usb_mass_copy_rule_fires(self):
        event = make_event(EventKind.FILE_WRITE, {"path": "/media/usb/dump.zip", "bytes": 80_000_000})
        alerts, updates = self.engine.evaluate(event, user_id="sara")
        rule_ids = [a.rule_id for a in alerts]
        self.assertIn("R-USB-001", rule_ids)
        self.assertTrue(any(u.subject_kind == "user" and u.subject_id == "sara" for u in updates))

    def test_usb_mass_copy_does_not_fire_below_threshold(self):
        event = make_event(EventKind.FILE_WRITE, {"path": "/media/usb/dump.zip", "bytes": 1024})
        alerts, _ = self.engine.evaluate(event)
        self.assertFalse(any(a.rule_id == "R-USB-001" for a in alerts))

    def test_c2_callout_via_ioc(self):
        event = make_event(EventKind.NETWORK_CONNECT, {"domain": "malware-c2.example", "ip": "10.0.0.1"})
        alerts, _ = self.engine.evaluate(event)
        ids = [a.rule_id for a in alerts]
        self.assertIn("R-NET-001", ids)

    def test_ioc_sha256_match(self):
        self.engine.add_ioc("sha256", "deadbeef")
        event = make_event(EventKind.FILE_WRITE, {"path": "/tmp/x", "bytes": 10, "sha256": "DEADBEEF"})
        alerts, _ = self.engine.evaluate(event)
        self.assertTrue(any(a.rule_id == "IOC-SHA256" for a in alerts))

    def test_ueba_anomaly_after_baseline(self):
        for _ in range(15):
            self.engine.evaluate(make_event(EventKind.FILE_WRITE, {"path": "/home/x", "bytes": 100}))
        spike = make_event(EventKind.FILE_WRITE, {"path": "/home/x", "bytes": 50_000_000})
        alerts, _ = self.engine.evaluate(spike, user_id="sara")
        self.assertTrue(any(a.rule_id == "UEBA-Z" for a in alerts), msg=str([a.rule_id for a in alerts]))

    def test_risk_blends_per_user(self):
        event = make_event(EventKind.FILE_WRITE, {"path": "/media/usb/x", "bytes": 80_000_000})
        self.engine.evaluate(event, user_id="sara")
        first = self.engine.risk_for_user("sara")
        self.engine.evaluate(event, user_id="sara")
        second = self.engine.risk_for_user("sara")
        self.assertGreater(second, first)

    def test_ransomware_extension_pattern(self):
        event = make_event(EventKind.FILE_WRITE, {"path": "/home/me/file.locked", "bytes": 1000})
        alerts, _ = self.engine.evaluate(event)
        self.assertTrue(any(a.rule_id == "R-FILE-001" for a in alerts))


if __name__ == "__main__":
    unittest.main()

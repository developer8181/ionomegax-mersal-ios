import unittest

from eig.audit_chain import GENESIS_HASH, append_entry, verify_chain


class AuditChainTests(unittest.TestCase):
    def test_chain_verifies(self) -> None:
        first = append_entry(
            sequence=1,
            event_type="test",
            payload={"a": 1},
            previous_hash=GENESIS_HASH,
            created_at="2026-05-27T12:00:00+00:00",
        )
        second = append_entry(
            sequence=2,
            event_type="test",
            payload={"b": 2},
            previous_hash=first.entry_hash,
            created_at="2026-05-27T12:01:00+00:00",
        )
        result = verify_chain([first, second])
        self.assertTrue(result["valid"])

    def test_tamper_detected(self) -> None:
        entry = append_entry(
            sequence=1,
            event_type="test",
            payload={"x": 1},
            previous_hash=GENESIS_HASH,
            created_at="2026-05-27T12:00:00+00:00",
        )
        broken = append_entry(
            sequence=2,
            event_type="test",
            payload={"y": 2},
            previous_hash="deadbeef",
            created_at="2026-05-27T12:01:00+00:00",
        )
        self.assertFalse(verify_chain([entry, broken])["valid"])


if __name__ == "__main__":
    unittest.main()

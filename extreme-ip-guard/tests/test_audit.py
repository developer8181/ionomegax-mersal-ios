import unittest

from xig.audit import AuditChain, GENESIS_HASH


class AuditChainTests(unittest.TestCase):
    def test_chain_grows_and_verifies(self):
        chain = AuditChain()
        self.assertEqual(chain.last_hash, GENESIS_HASH)
        records = []
        for i in range(5):
            payload = {"ts": f"t{i}", "actor": "test", "action": "noop", "target": "", "data": {"i": i}}
            stored = chain.append(payload)
            row = {**stored.payload, "prev_hash": stored.prev_hash, "chain_hash": stored.chain_hash}
            records.append(row)
        ok, broken = AuditChain.verify(records)
        self.assertTrue(ok)
        self.assertEqual(broken, -1)

    def test_chain_detects_tampering(self):
        chain = AuditChain()
        records = []
        for i in range(3):
            stored = chain.append({"i": i, "action": "noop"})
            records.append({**stored.payload, "prev_hash": stored.prev_hash, "chain_hash": stored.chain_hash})
        records[1]["i"] = 999
        ok, broken = AuditChain.verify(records)
        self.assertFalse(ok)
        self.assertEqual(broken, 1)

    def test_checkpoint_returns_root(self):
        chain = AuditChain()
        records = []
        for i in range(4):
            stored = chain.append({"i": i})
            records.append({"chain_hash": stored.chain_hash})
        checkpoint = AuditChain.checkpoint(records)
        self.assertEqual(checkpoint["count"], 4)
        self.assertEqual(len(checkpoint["merkle_root"]), 64)


if __name__ == "__main__":
    unittest.main()

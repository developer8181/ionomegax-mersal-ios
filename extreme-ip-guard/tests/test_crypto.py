import unittest

from xig.crypto import (
    AgentKeyPair,
    chain_hash,
    hash_password,
    merkle_root,
    sha256_hex,
    sign_blob,
    verify_blob,
    verify_password,
)


class CryptoTests(unittest.TestCase):
    def test_password_roundtrip(self):
        stored = hash_password("hunter2")
        self.assertTrue(verify_password("hunter2", stored))
        self.assertFalse(verify_password("wrong", stored))

    def test_sign_and_verify(self):
        kp = AgentKeyPair.generate("agent-1")
        payload = {"kind": "event", "agent_id": "agent-1", "n": 7}
        signature = sign_blob(kp.secret, payload)
        self.assertTrue(verify_blob(kp.secret, payload, signature))
        self.assertFalse(verify_blob(kp.secret, {"kind": "tampered"}, signature))

    def test_sign_returns_versioned_format(self):
        kp = AgentKeyPair.generate("agent-1")
        sig = sign_blob(kp.secret, {"a": 1})
        self.assertTrue(sig.startswith("HMAC-SHA256:"))

    def test_verify_rejects_malformed_signature(self):
        kp = AgentKeyPair.generate("agent-1")
        self.assertFalse(verify_blob(kp.secret, {}, ""))
        self.assertFalse(verify_blob(kp.secret, {}, "garbage"))
        self.assertFalse(verify_blob(kp.secret, {}, "RSA:zzz"))

    def test_chain_hash_changes_with_inputs(self):
        h1 = chain_hash("aaa", {"x": 1})
        h2 = chain_hash("aaa", {"x": 2})
        h3 = chain_hash("bbb", {"x": 1})
        self.assertNotEqual(h1, h2)
        self.assertNotEqual(h1, h3)
        self.assertEqual(len(h1), 64)

    def test_merkle_root_handles_empty_and_odd(self):
        self.assertEqual(merkle_root([]), sha256_hex(""))
        odd = [sha256_hex("a"), sha256_hex("b"), sha256_hex("c")]
        even = [sha256_hex("a"), sha256_hex("b"), sha256_hex("c"), sha256_hex("c")]
        self.assertEqual(merkle_root(odd), merkle_root(even))


if __name__ == "__main__":
    unittest.main()

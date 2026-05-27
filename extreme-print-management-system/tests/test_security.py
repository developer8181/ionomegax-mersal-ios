import unittest

from epms.security import is_authorized_agent_token


class SecurityTests(unittest.TestCase):
    def test_allows_requests_when_token_enforcement_is_disabled(self):
        self.assertTrue(is_authorized_agent_token(None, None))
        self.assertTrue(is_authorized_agent_token("", ""))

    def test_validates_configured_agent_token(self):
        self.assertTrue(is_authorized_agent_token("secret-token", "secret-token"))
        self.assertFalse(is_authorized_agent_token("wrong", "secret-token"))
        self.assertFalse(is_authorized_agent_token(None, "secret-token"))


if __name__ == "__main__":
    unittest.main()

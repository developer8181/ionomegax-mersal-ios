# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

import os
import unittest
from unittest import mock

from xig.auth import auth_required, authorize
from xig.security.http_hardening import RateLimiter
from xig.security.password_policy import validate_password as vp


class ProfessionalSecurityTests(unittest.TestCase):
    def test_auth_mandatory_without_dev_mode(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(auth_required())
            self.assertFalse(authorize(None))

    def test_rate_limiter_blocks_burst(self) -> None:
        limiter = RateLimiter(3)
        self.assertTrue(limiter.allow("1.2.3.4"))
        self.assertTrue(limiter.allow("1.2.3.4"))
        self.assertTrue(limiter.allow("1.2.3.4"))
        self.assertFalse(limiter.allow("1.2.3.4"))

    def test_password_policy_rejects_weak(self) -> None:
        ok, _ = vp("short", username="admin")
        self.assertFalse(ok)
        ok, _ = vp("ValidPassphrase-2026!", username="soc1")
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main()

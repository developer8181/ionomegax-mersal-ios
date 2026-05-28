# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.
# Arabic: تم التصميم والبرمجة بواسطة المهندس محمود راسم بياري — رام الله، فلسطين.
import os
import unittest
from unittest import mock

from xig.auth import (
    auth_required,
    authorize,
    create_session_token,
    verify_admin,
    verify_session_token,
)


class AuthTests(unittest.TestCase):
    def test_open_when_no_secrets(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(auth_required())
            self.assertTrue(authorize(None))

    def test_api_token_authorization(self):
        with mock.patch.dict(os.environ, {"MERSAL_API_TOKEN": "secret-token"}, clear=True):
            self.assertTrue(auth_required())
            self.assertTrue(authorize("secret-token"))
            self.assertFalse(authorize("wrong"))

    def test_admin_login_and_session(self):
        with mock.patch.dict(
            os.environ,
            {"MERSAL_ADMIN_PASSWORD": "admin-pass", "MERSAL_ADMIN_USER": "root"},
            clear=True,
        ):
            self.assertTrue(verify_admin("root", "admin-pass"))
            self.assertFalse(verify_admin("root", "bad"))
            token = create_session_token("root")
            self.assertTrue(verify_session_token(token))
            self.assertTrue(authorize(token))


if __name__ == "__main__":
    unittest.main()

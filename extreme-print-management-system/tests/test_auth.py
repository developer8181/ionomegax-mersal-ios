import unittest

from epms.auth import AdminUser, hash_password, verify_password


class AuthTests(unittest.TestCase):
    def test_password_hash_round_trip(self):
        encoded = hash_password("secret-pass")
        self.assertTrue(verify_password("secret-pass", encoded))
        self.assertFalse(verify_password("wrong", encoded))

    def test_role_permissions(self):
        admin = AdminUser(id=1, username="admin", role="admin", display_name="Admin")
        viewer = AdminUser(id=2, username="view", role="viewer", display_name="View")
        self.assertTrue(admin.has_permission("manage_jobs"))
        self.assertFalse(viewer.has_permission("manage_jobs"))
        self.assertTrue(viewer.has_permission("view"))


if __name__ == "__main__":
    unittest.main()

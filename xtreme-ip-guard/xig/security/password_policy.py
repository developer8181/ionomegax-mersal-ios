# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Password policy aligned with NIST SP 800-63B style guidance for organizations."""

from __future__ import annotations

import re


def validate_password(password: str, *, username: str = "") -> tuple[bool, str]:
    if len(password) < 12:
        return False, "password must be at least 12 characters"
    if username and username.lower() in password.lower():
        return False, "password must not contain username"
    classes = sum(
        [
            bool(re.search(r"[a-z]", password)),
            bool(re.search(r"[A-Z]", password)),
            bool(re.search(r"[0-9]", password)),
            bool(re.search(r"[^A-Za-z0-9]", password)),
        ]
    )
    if classes < 3:
        return False, "password must use at least 3 character classes (upper, lower, digit, symbol)"
    common = {"password", "123456789012", "mersal123456", "admin12345678"}
    if password.lower() in common:
        return False, "password is too common"
    return True, ""

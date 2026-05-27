"""Optional API token authentication for Mersal Guard."""

from __future__ import annotations

import os
import secrets


def configured_token() -> str:
    return os.environ.get("MERSAL_API_TOKEN", os.environ.get("XIG_API_TOKEN", "")).strip()


def authorize(header_value: str | None) -> bool:
    expected = configured_token()
    if not expected:
        return True
    if not header_value:
        return False
    return secrets.compare_digest(header_value.strip(), expected)

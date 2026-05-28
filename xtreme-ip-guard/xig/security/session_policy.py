# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Session lifetime policy — shorter TTL for regulated enterprise."""

from __future__ import annotations

import os

from ..config import is_enterprise, is_production


def session_ttl_seconds() -> int:
    raw = os.environ.get("MERSAL_SESSION_TTL_SECONDS", "").strip()
    if raw.isdigit():
        return max(300, int(raw))
    if is_enterprise() and is_production():
        return 28_800  # 8 hours
    return 86_400

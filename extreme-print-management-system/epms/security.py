"""Security helpers for production-oriented agent communication."""

from __future__ import annotations

import hmac


AGENT_TOKEN_HEADER = "X-EPMS-Agent-Token"


def is_authorized_agent_token(provided: str | None, expected: str | None) -> bool:
    """Validate an agent token when token enforcement is configured."""
    if not expected:
        return True
    if not provided:
        return False
    return hmac.compare_digest(provided, expected)

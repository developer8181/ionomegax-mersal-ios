# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Map IdP groups/claims to Mersal RBAC roles — bank/government SSO."""

from __future__ import annotations

import json
import os
from typing import Any


def load_group_role_map(env_key: str = "MERSAL_GROUP_ROLE_MAP") -> dict[str, str]:
    raw = os.environ.get(env_key, "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def resolve_role_from_claims(
    claims: dict[str, Any],
    *,
    default_role: str = "analyst",
    group_claim_keys: tuple[str, ...] = ("groups", "roles", "memberOf", "group"),
) -> str:
    mapping = load_group_role_map()
    if not mapping:
        return default_role
    groups: list[str] = []
    for key in group_claim_keys:
        value = claims.get(key)
        if isinstance(value, list):
            groups.extend(str(g) for g in value)
        elif isinstance(value, str) and value:
            groups.append(value)
    for group in groups:
        if group in mapping:
            return mapping[group]
        for pattern, role in mapping.items():
            if pattern.endswith("*") and group.startswith(pattern[:-1]):
                return role
    return default_role

# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Optional LDAP / Active Directory authentication for enterprise deployments."""

from __future__ import annotations

import os
from typing import Any


def ldap_configured() -> bool:
    return bool(os.environ.get("MERSAL_LDAP_URL", "").strip())


def authenticate_ldap(username: str, password: str) -> dict[str, Any] | None:
    """Bind against LDAP; returns role mapping on success."""
    url = os.environ.get("MERSAL_LDAP_URL", "").strip()
    if not url or not username or not password:
        return None
    base_dn = os.environ.get("MERSAL_LDAP_BASE_DN", "").strip()
    bind_dn = os.environ.get("MERSAL_LDAP_BIND_DN", "").strip()
    bind_pw = os.environ.get("MERSAL_LDAP_BIND_PASSWORD", "").strip()
    user_filter = os.environ.get("MERSAL_LDAP_USER_FILTER", "(uid={username})")
    default_role = os.environ.get("MERSAL_LDAP_DEFAULT_ROLE", "analyst").strip() or "analyst"
    try:
        import ldap3  # type: ignore[import-untyped]
    except ImportError:
        return None

    server = ldap3.Server(url, get_info=ldap3.NONE)
    user_dn = None
    try:
        if bind_dn and bind_pw:
            conn = ldap3.Connection(server, bind_dn, bind_pw, auto_bind=True)
            filt = user_filter.format(username=username)
            conn.search(base_dn, filt, attributes=["cn", "memberOf"])
            if not conn.entries:
                return None
            user_dn = conn.entries[0].entry_dn
            conn.unbind()
        conn = ldap3.Connection(server, user_dn or f"uid={username},{base_dn}", password, auto_bind=True)
        if not conn.bind():
            return None
        role = _map_role(conn, default_role)
        conn.unbind()
        return {"username": username, "role": role, "tenant_id": "default", "auth": "ldap"}
    except Exception:  # noqa: BLE001
        return None


def _map_role(conn: Any, default: str) -> str:
    groups = os.environ.get("MERSAL_LDAP_SOC_ADMIN_GROUP", "").strip()
    if groups and conn.user:
        member_of = str(getattr(conn.user, "memberOf", "") or "")
        if groups in member_of:
            return "soc_admin"
    return default

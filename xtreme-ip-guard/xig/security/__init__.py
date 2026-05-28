# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Enterprise security — access control and route policy."""

from .access import AccessContext, permission_for_route, resolve_access

__all__ = ["AccessContext", "permission_for_route", "resolve_access"]

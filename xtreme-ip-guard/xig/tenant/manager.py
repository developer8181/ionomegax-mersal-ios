# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Multi-tenant management — MSP / workspace isolation."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..storage import Database


class TenantManager:
    def __init__(self, database: "Database") -> None:
        self.db = database
        self.db.ensure_default_tenant()

    def create(self, name: str, *, slug: str = "", plan: str = "enterprise", region: str = "global") -> dict[str, Any]:
        slug = slug or self._slugify(name)
        tenant_id = f"tenant-{slug}"[:48]
        return self.db.create_tenant(tenant_id=tenant_id, name=name, slug=slug, plan=plan, region=region)

    def list_all(self) -> list[dict[str, Any]]:
        return self.db.list_tenants()

    def dashboard(self) -> dict[str, Any]:
        tenants = self.list_all()
        return {
            "module": "Mersal Multi-Tenant",
            "tenants_count": len(tenants),
            "tenants": tenants,
            "default_tenant": "default",
        }

    @staticmethod
    def _slugify(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        return slug[:32] or "org"

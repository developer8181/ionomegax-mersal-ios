# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Public platform summary — safe for unauthenticated status pages."""

from __future__ import annotations

from .. import __version__
from ..config import is_enterprise, is_production
from ..db.adapter import uses_postgres


def public_platform_summary() -> dict[str, object]:
    return {
        "product": "Ionomegax Mersal Global Security Platform",
        "version": __version__,
        "production_mode": is_production(),
        "enterprise_mode": is_enterprise(),
        "postgres_backend": uses_postgres(),
        "integration_tier": "complete-unified-advanced",
        "reliability_api": "/api/platform/reliability",
        "evidence_pack_api": "/api/compliance/evidence-pack",
        "capabilities_count": 16,
        "console": "/console/",
        "docs": {
            "complete_ar": "docs/MERSAL_v8_7_COMPLETE_PLATFORM_AR.md",
            "enterprise_ha_ar": "docs/MERSAL_v8_6_ENTERPRISE_HA_AR.md",
        },
        "api": {
            "readiness": "/api/system/readiness",
            "enterprise_readiness": "/api/system/enterprise-readiness",
            "unified": "/api/platform/unified",
            "build": "/api/system/build",
        },
    }

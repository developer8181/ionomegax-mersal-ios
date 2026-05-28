# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Production readiness report — real checks, no mock status."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Any

from . import __version__
from .config import allow_demo_seed, is_production, tls_enabled
from .vuln.kev_feed import fetch_kev_indicators
from .vuln.nmap_probe import nmap_available

if TYPE_CHECKING:
    from .storage import Database


def production_readiness(database: "Database") -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str, *, required: bool = True) -> None:
        checks.append({"name": name, "ok": ok, "detail": detail, "required": required})

    add("production_mode", is_production(), "MERSAL_PRODUCTION=1" if is_production() else "development mode")
    add(
        "demo_seed_disabled",
        not (is_production() and allow_demo_seed()),
        "no toy demo seed unless MERSAL_DEMO_UI=1",
    )
    add("auth_configured", _auth_ok(), "API token or admin password set")
    add("policies_present", len(database.list_policies()) >= 1, f"{len(database.list_policies())} policies")
    add("endpoints_registered", len(database.list_endpoints()) >= 1, f"{len(database.list_endpoints())} endpoints")
    add("threat_intel_loaded", len(database.list_threat_intel()) >= 5, "threat intel cache populated")
    add("tls_optional", tls_enabled(), "HTTPS via MERSAL_TLS_CERT/KEY", required=False)
    add("nmap_scanner", nmap_available(), "nmap on PATH for network discovery", required=False)
    add("kev_feed_reachable", _kev_reachable(), "CISA KEV catalog fetch", required=False)

    required_checks = [c for c in checks if c["required"]]
    passed = sum(1 for c in required_checks if c["ok"])
    ready = passed == len(required_checks) and is_production()

    return {
        "version": __version__,
        "production_mode": is_production(),
        "ready_for_trial": ready,
        "checks_passed": passed,
        "checks_total": len(required_checks),
        "checks": checks,
        "posture": database.latest_security_posture(),
        "modules": [
            "neural_cortex",
            "vulnerability_management",
            "threat_intelligence_cisa_kev",
            "soar",
            "edr_lite",
            "daily_scheduler",
        ],
    }


def _auth_ok() -> bool:
    from .auth import admin_password, configured_token

    return bool(configured_token() or admin_password())


def _kev_reachable() -> bool:
    import os

    url = os.environ.get(
        "MERSAL_KEV_FEED_URL",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    ).strip()
    try:
        indicators = fetch_kev_indicators(url, timeout=8)
        return len(indicators) > 10
    except Exception:  # noqa: BLE001
        return False


def tool_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for tool in ("nmap", "openssl", "python3"):
        path = shutil.which(tool)
        versions[tool] = path or "not_installed"
    return versions

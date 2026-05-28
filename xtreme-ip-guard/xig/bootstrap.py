# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""First-run organization bootstrap — real policies, threat feeds, no toy demo mode."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .core import PolicyRule
from .fabric import MersalSecurityFabric

if TYPE_CHECKING:
    from .storage import Database


ENTERPRISE_POLICIES: tuple[PolicyRule, ...] = (
    PolicyRule(
        rule_id="MERSAL-DLP-USB-SECRET",
        name="Block secret data on removable media",
        action="block",
        event_type="file_copy",
        classification="secret",
        channel="removable_media",
        reason="Enterprise policy: secret data cannot leave on USB",
    ),
    PolicyRule(
        rule_id="MERSAL-DLP-MAIL-CONFIDENTIAL",
        name="Quarantine confidential personal email",
        action="quarantine",
        classification="confidential",
        channel="personal_email",
        reason="Confidential data to personal email requires review",
    ),
    PolicyRule(
        rule_id="MERSAL-CLOUD-SOURCE-BLOCK",
        name="Block source code to unsanctioned cloud",
        action="block",
        classification="source_code",
        channel="unsanctioned_cloud",
        reason="Source code restricted to approved repositories",
    ),
    PolicyRule(
        rule_id="MERSAL-CREDENTIAL-ISOLATE",
        name="Isolate credential exfiltration",
        action="isolate_endpoint",
        classification="credential",
        min_risk=75,
        reason="Credential movement at high risk",
    ),
    PolicyRule(
        rule_id="MERSAL-RANSOM-PROCESS",
        name="Block suspected ransomware process patterns",
        action="block",
        event_type="process_alert",
        classification="malware",
        min_risk=60,
        reason="EDR: suspicious process behavior",
    ),
)


def bootstrap_organization(database: "Database", *, site_name: str = "Primary Site") -> dict[str, Any]:
    """Initialize production tenant: policies, threat intel, first scan cycle."""
    _register_management_endpoint(database, site_name=site_name)
    for policy in ENTERPRISE_POLICIES:
        try:
            database.create_policy(policy)
        except Exception:  # noqa: BLE001 — policy may exist
            pass

    fabric = MersalSecurityFabric(database)
    feeds = fabric.feeds.sync_all(remote_url=_kev_feed_url())
    scan = fabric.scanner.scan_all_endpoints(scope="bootstrap")
    daily = fabric.run_daily_now()

    return {
        "site": site_name,
        "policies_installed": len(ENTERPRISE_POLICIES),
        "threat_feeds": feeds,
        "vulnerability_scan": {"findings_count": scan.get("findings_count", 0)},
        "daily_cycle": daily,
        "posture": database.latest_security_posture(),
    }


def _kev_feed_url() -> str:
    import os

    return os.environ.get(
        "MERSAL_KEV_FEED_URL",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    ).strip()


def _register_management_endpoint(database: "Database", *, site_name: str) -> None:
    from .platform import collect_profile
    from .platform.vuln_probe import collect_vuln_probe

    profile = collect_profile()
    endpoint_id = f"mgmt-{profile.hostname}".lower().replace(" ", "-")[:64]
    database.record_agent_heartbeat(
        agent_id=f"mersal-mgmt-{profile.hostname}",
        agent_type="management",
        hostname=profile.hostname,
        os_name=profile.os_name,
        version="3.0.0",
        metadata={
            "endpoint_id": endpoint_id,
            "owner": "security-ops",
            "site": site_name,
            "role": "management_node",
            "security_features": profile.security_features,
            "sensors": profile.sensors,
            "vuln_probe": profile.sensors.get("vuln_probe")
            or collect_vuln_probe(profile.security_features),
        },
    )

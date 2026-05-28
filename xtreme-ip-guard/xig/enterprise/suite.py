# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Mersal Enterprise Security Suite — unified alternative to fragmented SOC stacks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..compliance import ComplianceEngine
from ..incidents import IncidentManager
from ..network import FirewallManager
from ..siem import SiemCorrelator

if TYPE_CHECKING:
    from ..fabric import MersalSecurityFabric
    from ..storage import Database


class MersalEnterpriseSuite:
    """
    Integrated modules replacing separate EDR + SIEM + SOAR + GRC + NGFW consoles:
    - Mersal SIEM
    - Mersal EDR (process + network + FIM)
    - Mersal Incident Response
    - Mersal Compliance (NIST-CSF)
    - Mersal Network Security
    - Mersal Global Security Fabric (AI, vuln, threat, SOAR)
    """

    def __init__(self, database: "Database", fabric: "MersalSecurityFabric | None" = None) -> None:
        self.db = database
        self.fabric = fabric
        self.siem = SiemCorrelator(database)
        self.incidents = IncidentManager(database)
        self.compliance = ComplianceEngine(database)
        self.firewall = FirewallManager(database)

    def run_enterprise_cycle(self) -> dict[str, Any]:
        results: dict[str, Any] = {}
        if self.fabric:
            results["threat_feeds"] = self.fabric.feeds.sync_all(
                kev_url=_kev_url_for_sync(),
            )
            results["vuln_scan"] = self.fabric.scanner.scan_all_endpoints(scope="enterprise")
            results["ai_train"] = self.db.train_cortex_from_history(limit=200)
            from ..fabric.posture import compute_posture

            results["posture"] = compute_posture(self.db)
        results["siem_retro"] = self.siem.run_retrospective(limit=100)
        results["compliance"] = self.compliance.assess()
        results["edr"] = self._run_edr_sweep()
        results["network_policy"] = self.firewall.build_policy()
        return results

    def _run_edr_sweep(self) -> dict[str, Any]:
        from ..edr.network_intel import collect_network_connections, suspicious_flows
        from ..edr.process_intel import collect_running_processes, suspicious_process_events
        from ..platform import collect_profile

        profile = collect_profile()
        endpoint_id = f"mgmt-{profile.hostname}".lower()[:64]
        detections = 0

        for event in suspicious_process_events(collect_running_processes(limit=35)):
            self.db.record_edr_detection(
                endpoint_id=endpoint_id,
                detection_type="process",
                severity=int(event.severity) + 40,
                title=f"Suspicious process: {event.resource}",
                details=dict(event.metadata),
            )
            detections += 1

        flows = collect_network_connections()
        self.db.record_network_flows(endpoint_id, flows)
        for flow in suspicious_flows(flows):
            self.db.record_edr_detection(
                endpoint_id=endpoint_id,
                detection_type="network",
                severity=int(flow.get("risk", 50)),
                title=f"Suspicious connection: {flow.get('remote_addr')}",
                details=flow,
            )
            detections += 1

        return {"endpoint": endpoint_id, "detections_recorded": detections, "flows": len(flows)}

    def dashboard(self) -> dict[str, Any]:
        fabric_dash = self.fabric.dashboard() if self.fabric else {}
        return {
            "suite": "Mersal Enterprise Security Suite",
            "version": "4.0",
            "positioning": "Integrated alternative to EDR + SIEM + SOAR + VM + GRC stacks",
            "modules": {
                "fabric": fabric_dash,
                "siem": self.siem.dashboard(),
                "incidents": self.incidents.dashboard(),
                "compliance": self.compliance.dashboard(),
                "network": self.firewall.dashboard(),
                "edr": {
                    "open_detections": len(self.db.list_edr_detections(limit=50)),
                    "recent": self.db.list_edr_detections(limit=10),
                },
            },
            "posture": self.db.latest_security_posture(),
        }

    def comparison_matrix(self) -> list[dict[str, str]]:
        return [
            {"capability": "Endpoint DLP", "mersal": "Built-in policies + enforcement", "legacy": "Separate DLP appliance"},
            {"capability": "EDR", "mersal": "Process + network + FIM", "legacy": "CrowdStrike / Defender"},
            {"capability": "SIEM", "mersal": "Real-time correlation rules", "legacy": "Splunk / QRadar"},
            {"capability": "SOAR", "mersal": "Playbooks + auto-isolate", "legacy": "Palo Alto XSOAR"},
            {"capability": "Vulnerability Mgmt", "mersal": "Daily scan + CISA KEV", "legacy": "Nessus / Qualys"},
            {"capability": "Threat Intel", "mersal": "STIX + CISA KEV", "legacy": "Recorded Future feed"},
            {"capability": "Compliance", "mersal": "NIST-CSF assessment", "legacy": "GRC platform"},
            {"capability": "AI Defense", "mersal": "Neural Cortex on-prem", "legacy": "Cloud ML add-on"},
        ]


def _kev_url_for_sync() -> str:
    import os

    explicit = os.environ.get("MERSAL_KEV_FEED_URL")
    if explicit is not None and explicit.strip() == "":
        return ""
    if explicit:
        return explicit.strip()
    return "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

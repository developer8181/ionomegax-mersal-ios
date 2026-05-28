#!/usr/bin/env python3
# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Populate demo database with rich v5.0 XDR data for screenshots and demos."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("MERSAL_KEV_FEED_URL", "")

from xig.compliance import ComplianceEngine  # noqa: E402
from xig.core import EndpointEvent  # noqa: E402
from xig.fabric import MersalSecurityFabric  # noqa: E402
from xig.siem.rules import DEFAULT_SIEM_RULES  # noqa: E402
from xig.storage import Database  # noqa: E402


def main() -> None:
    db_path = Path(os.environ.get("MERSAL_DB", ROOT / "data" / "demo-ui.sqlite3"))
    db = Database(db_path)
    db.init_schema()
    db.seed_demo()
    db.ensure_siem_rules(DEFAULT_SIEM_RULES)

    endpoints = [
        ("endpoint-demo-001", "FUTURE-LAPTOP-001", "Windows 11 Enterprise", "sara", 76),
        ("global-hq-gw-01", "MERSAL-GATEWAY-HQ", "Mersal OS 5.0", "noc", 88),
        ("global-fin-042", "FIN-SERVER-EU", "Linux RHEL 9", "finance", 71),
        ("global-dev-118", "DEV-WKS-APAC", "macOS 15", "devops", 68),
        ("global-soc-01", "SOC-ANALYST-01", "Mersal XDR Console", "soc", 92),
    ]
    for eid, host, os_name, owner, trust in endpoints:
        db.record_agent_heartbeat(
            agent_id=f"agent-{eid}",
            agent_type="endpoint",
            hostname=host,
            os_name=os_name,
            version="5.0.0",
            metadata={
                "endpoint_id": eid,
                "owner": owner,
                "site": "Global HQ",
                "vuln_probe": {
                    "open_ports": [22, 443, 445] if "gw" in eid else [22, 8080, 3389],
                    "security_features": {"disk_encryption": "gw" in eid or "soc" in eid},
                },
            },
        )
        with db.connect() as conn:
            conn.execute("UPDATE endpoints SET trust_score = ? WHERE endpoint_id = ?", (trust, eid))

    samples = [
        EndpointEvent(
            endpoint_id="global-fin-042",
            actor="sara",
            event_type="file_copy",
            channel="removable_media",
            resource="/finance/annual-report.xlsx",
            classification="secret",
            destination="usb:Samsung",
            severity=30,
        ),
        EndpointEvent(
            endpoint_id="global-dev-118",
            actor="omar",
            event_type="network_upload",
            channel="unsanctioned_cloud",
            resource="credentials.zip",
            classification="credential",
            destination="https://pastebin.com/raw/demo",
            severity=40,
            behavior_flags=("mass_file_access",),
        ),
        EndpointEvent(
            endpoint_id="endpoint-demo-001",
            actor="admin",
            event_type="network_upload",
            channel="personal_email",
            resource="contract.pdf",
            classification="confidential",
            destination="https://gmail.com/send",
            severity=22,
        ),
        EndpointEvent(
            endpoint_id="global-hq-gw-01",
            actor="noc",
            event_type="process_alert",
            channel="endpoint_process",
            resource="powershell.exe",
            classification="malware",
            destination="-enc JABXAG0AYwBhAGwA",
            severity=45,
            behavior_flags=("new_process", "unsigned_process"),
        ),
    ]
    for event in samples:
        db.ingest_event(event)

    db.create_siem_alert(
        rule_id="SIEM-CREDENTIAL-EXFIL",
        title="Credential exfiltration pattern",
        severity=90,
        endpoint_id="global-dev-118",
        details={"mitre_technique": "T1041", "rule": "SIEM-CREDENTIAL-EXFIL"},
    )
    db.create_siem_alert(
        rule_id="SIEM-RANSOMWARE-BEHAVIOR",
        title="Ransomware-like process activity",
        severity=95,
        endpoint_id="global-hq-gw-01",
        details={"mitre_technique": "T1486", "rule": "SIEM-RANSOMWARE-BEHAVIOR"},
    )
    db.create_siem_alert(
        rule_id="SIEM-AI-ESCALATION",
        title="AI cortex escalation",
        severity=85,
        endpoint_id="global-fin-042",
        details={"mitre_technique": "T1567", "rule": "SIEM-AI-ESCALATION"},
    )

    db.record_edr_detection(
        endpoint_id="global-hq-gw-01",
        detection_type="yara",
        severity=92,
        title="YARA: Encoded PowerShell",
        details={"rule_id": "YARA-POWERSHELL-ENC", "mitre": "T1059.001"},
    )
    db.record_edr_detection(
        endpoint_id="global-dev-118",
        detection_type="network",
        severity=78,
        title="Suspicious connection: 185.220.101.0:4444",
        details={"remote_addr": "185.220.101.0:4444"},
    )

    db.record_suricata_alert(
        {
            "signature_id": 2024001,
            "signature": "ET TROJAN Possible Cobalt Strike",
            "category": "trojan-activity",
            "severity": 75,
            "src_ip": "10.0.0.15",
            "dest_ip": "185.220.101.0",
            "proto": "TCP",
            "mitre_technique": "T1204.002",
        }
    )
    db.record_suricata_alert(
        {
            "signature_id": 2024002,
            "signature": "GPL EXPLOIT RDP brute force",
            "category": "attempted-admin",
            "severity": 60,
            "src_ip": "203.0.113.50",
            "dest_ip": "10.0.0.8",
            "proto": "TCP",
            "mitre_technique": "T1190",
        }
    )

    for i, msg in enumerate(
        [
            "auth failed for user admin from 203.0.113.50",
            "sudo: session opened for user root",
            "mersal-agent heartbeat OK global-hq-gw-01",
            "Suricata alert correlated to SIEM",
            "XDR policy: isolate_endpoint triggered",
        ]
    ):
        db.ingest_log_record(
            source="mersal-logvault",
            message=msg,
            host="global-hq-gw-01",
            severity=40 + i * 5,
            endpoint_id="global-hq-gw-01",
        )

    db.create_xdr_finding(
        title="XDR correlated threat on global-hq-gw-01",
        severity=94,
        endpoint_id="global-hq-gw-01",
        sources=["siem", "edr", "ids"],
        mitre_techniques=["T1486", "T1059.001"],
        recommended_action="isolate_endpoint",
        details={"siem": 2, "edr": 1, "ids": 1},
        confidence=0.92,
    )
    db.create_xdr_finding(
        title="XDR correlated threat on global-dev-118",
        severity=88,
        endpoint_id="global-dev-118",
        sources=["siem", "edr"],
        mitre_techniques=["T1041"],
        recommended_action="investigate",
        confidence=0.85,
    )

    db.create_incident(
        incident_id="INC-GLOBAL-HQ-001",
        title="Critical: Ransomware-like activity on gateway",
        severity="critical",
        endpoint_id="global-hq-gw-01",
        summary="Auto-opened from SIEM + XDR correlation",
    )
    db.add_incident_timeline(
        incident_id="INC-GLOBAL-HQ-001",
        entry_type="xdr",
        message="XDR finding created — multi-source correlation",
    )

    fabric = MersalSecurityFabric(db)
    fabric.feeds.sync_all(kev_url="")
    fabric.scanner.scan_all_endpoints(scope="demo")
    ComplianceEngine(db).assess()
    db.train_cortex_from_history(limit=80)

    db.record_audit("mersal-demo", "demo.seed", target="ui", details={"version": "5.0.0"})
    print(f"Demo UI database ready (v5.0 XDR): {db_path}")


if __name__ == "__main__":
    main()

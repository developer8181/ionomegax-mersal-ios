#!/usr/bin/env python3
"""Populate demo database with rich data for screenshots and demos."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from xig.core import EndpointEvent  # noqa: E402
from xig.fabric import MersalSecurityFabric  # noqa: E402
from xig.storage import Database  # noqa: E402


def main() -> None:
    db_path = Path(os.environ.get("MERSAL_DB", ROOT / "data" / "demo-ui.sqlite3"))
    db = Database(db_path)
    db.init_schema()
    db.seed_demo()

    endpoints = [
        ("endpoint-demo-001", "FUTURE-LAPTOP-001", "Windows 11 Enterprise", "sara", 76),
        ("egypt-hq-gw-01", "MERSAL-GATEWAY-CAIRO", "Mersal OS 2.0", "noc", 82),
        ("egypt-fin-042", "FIN-SERVER-ALEX", "Linux RHEL 9", "finance", 71),
        ("egypt-dev-118", "DEV-WKS-GIZA", "macOS 15", "devops", 68),
    ]
    for eid, host, os_name, owner, trust in endpoints:
        db.record_agent_heartbeat(
            agent_id=f"agent-{eid}",
            agent_type="endpoint",
            hostname=host,
            os_name=os_name,
            version="2.0.0",
            metadata={
                "endpoint_id": eid,
                "owner": owner,
                "site": "Cairo HQ",
                "vuln_probe": {
                    "open_ports": [22, 443, 445] if "gw" in eid else [22, 8080],
                    "security_features": {"disk_encryption": eid == "egypt-hq-gw-01"},
                },
            },
        )
        with db.connect() as conn:
            conn.execute("UPDATE endpoints SET trust_score = ? WHERE endpoint_id = ?", (trust, eid))

    samples = [
        EndpointEvent(
            endpoint_id="egypt-fin-042",
            actor="sara",
            event_type="file_copy",
            channel="removable_media",
            resource="/finance/annual-report.xlsx",
            classification="secret",
            destination="usb:Samsung",
            severity=30,
        ),
        EndpointEvent(
            endpoint_id="egypt-dev-118",
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
    ]
    for event in samples:
        db.ingest_event(event)

    fabric = MersalSecurityFabric(db)
    fabric.feeds.sync_all()
    fabric.scanner.scan_all_endpoints(scope="demo")
    fabric.run_daily_now()
    db.record_audit("mersal-demo", "demo.seed", target="ui", details={"version": "2.0.0"})
    print(f"Demo UI database ready: {db_path}")


if __name__ == "__main__":
    main()

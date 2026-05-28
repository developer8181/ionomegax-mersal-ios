# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""Built-in SIEM correlation rules — enterprise SOC patterns."""

from __future__ import annotations

from typing import Any

DEFAULT_SIEM_RULES: list[dict[str, Any]] = [
    {
        "rule_id": "SIEM-CREDENTIAL-EXFIL",
        "name": "Credential exfiltration pattern",
        "description": "High-risk credential movement to external destination",
        "severity": 90,
        "condition": {"classification": "credential", "min_risk": 75},
    },
    {
        "rule_id": "SIEM-RANSOMWARE-BEHAVIOR",
        "name": "Ransomware-like process activity",
        "description": "Process alert with malware classification",
        "severity": 95,
        "condition": {"event_type": "process_alert", "classification": "malware"},
    },
    {
        "rule_id": "SIEM-DLP-BLOCK-STORM",
        "name": "Repeated DLP blocks",
        "description": "Multiple block actions from same endpoint in short window",
        "severity": 70,
        "condition": {"action": "block", "window_blocks": 3},
    },
    {
        "rule_id": "SIEM-AI-ESCALATION",
        "name": "AI cortex escalation",
        "description": "Neural cortex escalated defensive action",
        "severity": 85,
        "condition": {"ai_escalated": True},
    },
    {
        "rule_id": "SIEM-IOC-MATCH",
        "name": "Threat intelligence IOC match",
        "description": "Destination matched known malicious indicator",
        "severity": 88,
        "condition": {"ioc_match": True},
    },
    {
        "rule_id": "SIEM-ISOLATION-EVENT",
        "name": "Endpoint isolation triggered",
        "description": "Automatic or policy-driven endpoint isolation",
        "severity": 80,
        "condition": {"action": "isolate_endpoint"},
    },
    {
        "rule_id": "SIEM-UNSANCTIONED-CLOUD",
        "name": "Data to unsanctioned cloud",
        "description": "Sensitive data uploaded to unapproved cloud storage",
        "severity": 75,
        "condition": {"channel": "unsanctioned_cloud", "min_risk": 50},
    },
]

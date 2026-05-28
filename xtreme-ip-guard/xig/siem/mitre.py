# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.
# Designed and developed by Eng. Mahmoud Rasem Bayari. All rights reserved.

"""MITRE ATT&CK technique mapping for alerts and XDR."""

from __future__ import annotations

RULE_TECHNIQUES: dict[str, str] = {
    "SIEM-CREDENTIAL-EXFIL": "T1041",
    "SIEM-RANSOMWARE-BEHAVIOR": "T1486",
    "SIEM-DLP-BLOCK-STORM": "T1020",
    "SIEM-AI-ESCALATION": "T1567",
    "SIEM-IOC-MATCH": "T1071",
    "SIEM-ISOLATION-EVENT": "T1486",
    "SIEM-UNSANCTIONED-CLOUD": "T1567.002",
}

EVENT_TECHNIQUES: dict[str, str] = {
    "process_alert": "T1059",
    "network_upload": "T1048",
    "file_copy": "T1052",
    "device_attached": "T1091",
}


def map_rule(rule_id: str) -> str:
    return RULE_TECHNIQUES.get(rule_id, "")


def map_event(event_type: str, classification: str = "") -> str:
    if classification == "credential":
        return "T1003"
    if classification == "malware":
        return "T1204"
    return EVENT_TECHNIQUES.get(event_type, "")


def map_suricata_category(category: str) -> str:
    cat = category.lower()
    if "trojan" in cat or "malware" in cat:
        return "T1204.002"
    if "exploit" in cat:
        return "T1190"
    if "command" in cat or "c2" in cat:
        return "T1071"
    return "T1595"

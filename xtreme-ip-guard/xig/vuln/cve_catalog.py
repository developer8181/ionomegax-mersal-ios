"""Curated CVE rules mapped to services and defensive misconfigurations."""

from __future__ import annotations

from typing import Any

# Representative high-impact CVEs for common exposed services (defensive correlation).
PORT_CVE_RULES: list[dict[str, Any]] = [
    {
        "cve_id": "CVE-2017-0144",
        "title": "SMBv1 remote code execution (EternalBlue class)",
        "port": 445,
        "service": "smb",
        "cvss": 10.0,
        "remediation": "Disable SMBv1; patch MS17-010; restrict port 445",
    },
    {
        "cve_id": "CVE-2021-44228",
        "title": "Log4Shell — JNDI injection in Java services",
        "port": 8080,
        "service": "http",
        "cvss": 10.0,
        "remediation": "Upgrade Log4j to 2.17.1+; block outbound LDAP",
    },
    {
        "cve_id": "CVE-2023-38408",
        "title": "OpenSSH PKCS#11 RCE (representative SSH hardening gap)",
        "port": 22,
        "service": "ssh",
        "cvss": 9.8,
        "remediation": "Patch OpenSSH; enforce key-only auth; fail2ban",
    },
    {
        "cve_id": "CVE-2019-0708",
        "title": "RDP BlueKeep — unauthenticated RCE",
        "port": 3389,
        "service": "rdp",
        "cvss": 9.8,
        "remediation": "Enable NLA; patch CVE-2019-0708; restrict RDP",
    },
    {
        "cve_id": "CVE-2020-1472",
        "title": "Zerologon — Netlogon elevation",
        "port": 445,
        "service": "netlogon",
        "cvss": 10.0,
        "remediation": "Apply August 2020 DC patches; monitor Netlogon",
    },
    {
        "cve_id": "CVE-2014-0160",
        "title": "OpenSSL Heartbleed — memory disclosure",
        "port": 443,
        "service": "https",
        "cvss": 7.5,
        "remediation": "Upgrade OpenSSL 1.0.1g+; rotate certificates",
    },
]

MISCONFIG_CHECKS: list[dict[str, Any]] = [
    {
        "check_id": "MERSAL-NO-DISK-ENCRYPTION",
        "title": "Disk encryption not detected",
        "cvss": 7.0,
        "remediation": "Enable LUKS/BitLocker/FileVault",
    },
    {
        "check_id": "MERSAL-LEGACY-OS",
        "title": "Legacy or unsupported OS pattern detected",
        "cvss": 8.0,
        "remediation": "Upgrade to supported OS release",
    },
    {
        "check_id": "MERSAL-RISKY-PORT-EXPOSED",
        "title": "High-risk service port exposed locally",
        "cvss": 8.5,
        "remediation": "Close unused ports; firewall restrict inbound",
    },
]

LEGACY_OS_MARKERS = ("windows 7", "windows xp", "ubuntu 16", "ubuntu 18.04", "debian 9", "centos 6")

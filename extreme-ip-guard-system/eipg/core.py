"""Core defensive policy rules for Extreme IP Guard.

The prototype intentionally models transparent enterprise protection workflows:
asset posture, risk scoring, DLP decisions, and response recommendations. It
does not implement stealth monitoring, credential collection, exploit logic, or
unauthorized network interception.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address


RISK_LEVELS = ("low", "medium", "high", "critical")


@dataclass(frozen=True)
class AssetPosture:
    encryption_enabled: bool = True
    edr_enabled: bool = True
    firewall_enabled: bool = True
    os_patch_age_days: int = 0
    critical_vulns: int = 0
    high_vulns: int = 0
    failed_login_count: int = 0
    dlp_incidents_24h: int = 0
    external_ip_exposure: bool = False
    sensitive_data_at_rest: bool = False
    unusual_egress_mb: int = 0


@dataclass(frozen=True)
class RiskDecision:
    risk_score: int
    risk_level: str
    action: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class DlpEvent:
    channel: str
    sensitivity: str
    destination_trusted: bool
    bytes_count: int = 0
    encrypted: bool = False
    user_override: bool = False


@dataclass(frozen=True)
class DataControlDecision:
    allowed: bool
    action: str
    severity: str
    reason: str


def evaluate_asset_posture(posture: AssetPosture) -> RiskDecision:
    """Score endpoint posture and choose a defensive response action."""
    _validate_non_negative(
        os_patch_age_days=posture.os_patch_age_days,
        critical_vulns=posture.critical_vulns,
        high_vulns=posture.high_vulns,
        failed_login_count=posture.failed_login_count,
        dlp_incidents_24h=posture.dlp_incidents_24h,
        unusual_egress_mb=posture.unusual_egress_mb,
    )

    score = 0
    reasons: list[str] = []

    if not posture.encryption_enabled:
        score += 15
        reasons.append("disk encryption is disabled")
    if not posture.edr_enabled:
        score += 20
        reasons.append("endpoint detection is disabled")
    if not posture.firewall_enabled:
        score += 10
        reasons.append("host firewall is disabled")

    if posture.os_patch_age_days > 90:
        score += 18
        reasons.append("operating system patches are older than 90 days")
    elif posture.os_patch_age_days > 45:
        score += 10
        reasons.append("operating system patches are older than 45 days")
    elif posture.os_patch_age_days > 14:
        score += 4
        reasons.append("operating system patches are older than 14 days")

    critical_vuln_score = min(posture.critical_vulns * 12, 30)
    high_vuln_score = min(posture.high_vulns * 4, 20)
    if critical_vuln_score:
        score += critical_vuln_score
        reasons.append(f"{posture.critical_vulns} critical vulnerability findings")
    if high_vuln_score:
        score += high_vuln_score
        reasons.append(f"{posture.high_vulns} high vulnerability findings")

    if posture.failed_login_count > 25:
        score += 15
        reasons.append("many failed logins were observed")
    elif posture.failed_login_count > 10:
        score += 8
        reasons.append("elevated failed login activity was observed")

    dlp_score = min(posture.dlp_incidents_24h * 5, 20)
    if dlp_score:
        score += dlp_score
        reasons.append(f"{posture.dlp_incidents_24h} DLP incidents in the last 24 hours")

    if posture.external_ip_exposure:
        score += 12
        reasons.append("asset exposes a public network service")
    if posture.sensitive_data_at_rest:
        score += 8
        reasons.append("sensitive data is stored locally")

    if posture.unusual_egress_mb > 1024:
        score += 15
        reasons.append("large unusual outbound transfer volume")
    elif posture.unusual_egress_mb > 256:
        score += 8
        reasons.append("unusual outbound transfer volume")

    score = min(score, 100)
    level = risk_level_for_score(score)
    action = action_for_risk_level(level)
    if not reasons:
        reasons.append("posture is within the approved baseline")
    return RiskDecision(risk_score=score, risk_level=level, action=action, reasons=tuple(reasons))


def risk_level_for_score(score: int) -> str:
    if score < 0 or score > 100:
        raise ValueError("risk score must be between 0 and 100")
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def action_for_risk_level(level: str) -> str:
    if level == "critical":
        return "isolate"
    if level == "high":
        return "restrict"
    if level == "medium":
        return "monitor"
    if level == "low":
        return "allow"
    raise ValueError(f"unknown risk level: {level}")


def evaluate_dlp_event(event: DlpEvent) -> DataControlDecision:
    """Decide how to handle a data movement attempt."""
    if event.bytes_count < 0:
        raise ValueError("bytes_count cannot be negative")

    channel = _normalize_token(event.channel)
    sensitivity = _normalize_token(event.sensitivity)
    if sensitivity not in {"public", "internal", "confidential", "secret"}:
        raise ValueError("sensitivity must be public, internal, confidential, or secret")

    high_risk_channel = channel in {"removable_media", "external_upload", "personal_email", "clipboard"}
    very_large_transfer = event.bytes_count >= 100 * 1024 * 1024

    if sensitivity == "public":
        return DataControlDecision(True, "allow", "low", "public data is allowed")

    if sensitivity == "secret" and not event.destination_trusted:
        return DataControlDecision(False, "deny", "critical", "secret data cannot leave trusted destinations")

    if sensitivity == "secret" and event.destination_trusted:
        return DataControlDecision(True, "require_approval", "high", "secret data requires explicit approval")

    if sensitivity == "confidential" and not event.destination_trusted:
        if event.encrypted and not very_large_transfer:
            return DataControlDecision(True, "require_approval", "medium", "encrypted confidential transfer needs approval")
        return DataControlDecision(False, "quarantine", "high", "confidential transfer to untrusted destination")

    if sensitivity == "internal" and not event.destination_trusted and (high_risk_channel or very_large_transfer):
        return DataControlDecision(True, "require_approval", "medium", "internal data is leaving through a high-risk path")

    if event.user_override and sensitivity in {"confidential", "secret"}:
        return DataControlDecision(False, "quarantine", "high", "user override attempted on sensitive data")

    return DataControlDecision(True, "monitor", "low", "event is allowed with audit monitoring")


def classify_ip_address(value: str) -> dict[str, str | bool]:
    """Classify an IP address without scanning or touching the network."""
    address = ip_address(value.strip())
    return {
        "ip": str(address),
        "version": f"IPv{address.version}",
        "is_private": address.is_private,
        "is_global": address.is_global,
        "is_loopback": address.is_loopback,
        "is_multicast": address.is_multicast,
        "is_reserved": address.is_reserved,
    }


def posture_from_dict(data: dict) -> AssetPosture:
    """Build posture from JSON-like data while applying safe defaults."""
    return AssetPosture(
        encryption_enabled=bool(data.get("encryption_enabled", True)),
        edr_enabled=bool(data.get("edr_enabled", True)),
        firewall_enabled=bool(data.get("firewall_enabled", True)),
        os_patch_age_days=int(data.get("os_patch_age_days", 0)),
        critical_vulns=int(data.get("critical_vulns", 0)),
        high_vulns=int(data.get("high_vulns", 0)),
        failed_login_count=int(data.get("failed_login_count", 0)),
        dlp_incidents_24h=int(data.get("dlp_incidents_24h", 0)),
        external_ip_exposure=bool(data.get("external_ip_exposure", False)),
        sensitive_data_at_rest=bool(data.get("sensitive_data_at_rest", False)),
        unusual_egress_mb=int(data.get("unusual_egress_mb", 0)),
    )


def _normalize_token(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _validate_non_negative(**values: int) -> None:
    for name, value in values.items():
        if value < 0:
            raise ValueError(f"{name} cannot be negative")


# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""SAML 2.0 assertion validation — Conditions, Audience, optional signature."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any


def verify_saml_response(
    xml_bytes: bytes,
    *,
    sp_entity_id: str,
    idp_cert_pem: str = "",
) -> tuple[bool, str, dict[str, Any]]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        return False, f"xml parse error: {exc}", {}

    name_id = ""
    for elem in root.iter():
        if elem.tag.endswith("NameID") and elem.text:
            name_id = elem.text.strip()
            break
    if not name_id:
        return False, "NameID missing", {}

    if not _conditions_valid(root):
        return False, "SAML Conditions expired or not yet valid", {}

    if sp_entity_id and not _audience_ok(root, sp_entity_id):
        return False, "AudienceRestriction mismatch", {}

    strict = os.environ.get("MERSAL_SAML_STRICT", "1").strip().lower() not in {"0", "false"}
    cert = idp_cert_pem.strip() or os.environ.get("MERSAL_SAML_IDP_CERT", "").strip()
    if strict and cert:
        ok, err = _verify_xml_signature(xml_bytes, cert)
        if not ok:
            return False, err, {}
    elif strict and not cert:
        return False, "MERSAL_SAML_IDP_CERT required when MERSAL_SAML_STRICT=1", {}

    claims = {"name_id": name_id}
    for elem in root.iter():
        if elem.tag.endswith("Attribute") and elem.get("Name"):
            values = [v.text for v in elem if v.text]
            if values:
                claims[elem.get("Name", "")] = values if len(values) > 1 else values[0]
    return True, "", claims


def _conditions_valid(root: ET.Element) -> bool:
    now = datetime.now(timezone.utc)
    for elem in root.iter():
        if not elem.tag.endswith("Conditions"):
            continue
        not_before = elem.get("NotBefore")
        not_on_or_after = elem.get("NotOnOrAfter")
        if not_before:
            if now < _parse_saml_time(not_before):
                return False
        if not_on_or_after:
            if now > _parse_saml_time(not_on_or_after):
                return False
    return True


def _audience_ok(root: ET.Element, audience: str) -> bool:
    for elem in root.iter():
        if elem.tag.endswith("Audience") and elem.text:
            if elem.text.strip() == audience:
                return True
    return not audience


def _parse_saml_time(value: str) -> datetime:
    text = value.replace("Z", "+00:00")
    return datetime.fromisoformat(text)


def _verify_xml_signature(xml_bytes: bytes, cert_pem: str) -> tuple[bool, str]:
    try:
        from signxml import XMLVerifier
        from cryptography.x509 import load_pem_x509_certificate
    except ImportError:
        return False, "install signxml and cryptography for SAML signature verification"
    try:
        cert = load_pem_x509_certificate(cert_pem.encode())
        XMLVerifier().verify(xml_bytes, x509_cert=cert)
        return True, ""
    except Exception as exc:  # noqa: BLE001
        return False, f"signature invalid: {exc}"

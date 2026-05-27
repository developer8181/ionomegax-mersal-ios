"""Konica Minolta OpenAPI SDK adapter."""

from __future__ import annotations

from .sdk_base import VendorSDKAdapter


class KonicaMinoltaOpenAPIAdapter(VendorSDKAdapter):
    vendor_key = "konica-minolta"
    sdk_module = "epms.embedded.konica"
    printer_prefix = "Konica Minolta"
    auth_pin_label = "openapi-pin"
    auth_card_label = "openapi-card"

"""Olivetti Connect / INFOchip SDK adapter."""

from __future__ import annotations

from .sdk_base import VendorSDKAdapter


class OlivettiConnectAdapter(VendorSDKAdapter):
    vendor_key = "olivetti"
    sdk_module = "epms.embedded.olivetti"
    printer_prefix = "Olivetti"
    auth_pin_label = "connect-pin"
    auth_card_label = "connect-card"

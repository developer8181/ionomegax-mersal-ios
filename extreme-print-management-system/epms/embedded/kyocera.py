"""Kyocera HyPAS SDK adapter."""

from __future__ import annotations

from .sdk_base import VendorSDKAdapter


class KyoceraHyPASAdapter(VendorSDKAdapter):
    vendor_key = "kyocera"
    sdk_module = "epms.embedded.kyocera"
    printer_prefix = "Kyocera"
    auth_pin_label = "hypas-pin"
    auth_card_label = "hypas-card"

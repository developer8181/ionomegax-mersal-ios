"""Canon MEAP SDK adapter."""

from __future__ import annotations

from .sdk_base import VendorSDKAdapter


class CanonMEAPAdapter(VendorSDKAdapter):
    vendor_key = "canon"
    sdk_module = "epms.embedded.canon"
    printer_prefix = "Canon"
    auth_pin_label = "meap-pin"
    auth_card_label = "meap-card"

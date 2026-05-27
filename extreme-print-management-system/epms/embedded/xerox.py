"""Xerox EIP SDK adapter."""

from __future__ import annotations

from .sdk_base import VendorSDKAdapter


class XeroxEIPAdapter(VendorSDKAdapter):
    vendor_key = "xerox"
    sdk_module = "epms.embedded.xerox"
    printer_prefix = "Xerox"
    auth_pin_label = "eip-pin"
    auth_card_label = "eip-card"

"""Lexmark eSF SDK adapter."""

from __future__ import annotations

from .sdk_base import VendorSDKAdapter


class LexmarkESFAdapter(VendorSDKAdapter):
    vendor_key = "lexmark"
    sdk_module = "epms.embedded.lexmark"
    printer_prefix = "Lexmark"
    auth_pin_label = "esf-pin"
    auth_card_label = "esf-card"

"""HP OXP / Workpath / FutureSmart SDK adapter."""

from __future__ import annotations

from .sdk_base import VendorSDKAdapter


class HPAdapter(VendorSDKAdapter):
    vendor_key = "hp"
    sdk_module = "epms.embedded.hp"
    printer_prefix = "HP"
    auth_pin_label = "oxp-pin"
    auth_card_label = "oxp-card"

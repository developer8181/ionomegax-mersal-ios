"""Ricoh SmartSDK adapter."""

from __future__ import annotations

from .sdk_base import VendorSDKAdapter


class RicohSmartSDKAdapter(VendorSDKAdapter):
    vendor_key = "ricoh"
    sdk_module = "epms.embedded.ricoh"
    printer_prefix = "Ricoh"
    auth_pin_label = "smartsdk-pin"
    auth_card_label = "smartsdk-card"

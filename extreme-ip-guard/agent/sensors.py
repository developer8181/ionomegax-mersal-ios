"""Reference sensors for the Extreme IP Guard endpoint agent.

Each sensor is a tiny function that produces a :class:`TelemetryEvent` (or
a list of them). The production implementations will be backed by OS-level
hooks; the simulators here let us exercise the control plane and the
detection engine deterministically from CI and from the CLI.
"""

from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass
from typing import Iterable

from xig.core import EventKind, TelemetryEvent, utc_now_iso


@dataclass(frozen=True)
class SensorContext:
    agent_id: str
    user: str = ""


def make_event(agent_id: str, kind: EventKind, subject: str, data: dict) -> TelemetryEvent:
    return TelemetryEvent(
        agent_id=agent_id,
        kind=kind.value,
        ts=utc_now_iso(),
        subject=subject,
        data=data,
    )


# ---- device sensor (USB) ----

def simulated_usb_mass_copy(ctx: SensorContext, *, bytes_written: int = 80_000_000) -> TelemetryEvent:
    return make_event(
        ctx.agent_id,
        EventKind.FILE_WRITE,
        subject="usb_mass_copy",
        data={
            "path": "/media/usb-1/financials-q4.zip",
            "bytes": int(bytes_written),
            "user": ctx.user,
        },
    )


def simulated_usb_attach(ctx: SensorContext, *, vendor: str = "Kingston", serial: str = "KGN-001") -> TelemetryEvent:
    return make_event(
        ctx.agent_id,
        EventKind.DEVICE_USB_ATTACH,
        subject=f"usb:{vendor}:{serial}",
        data={"vendor": vendor, "serial": serial, "interface": "Mass Storage"},
    )


# ---- process sensor ----

def simulated_office_spawned_shell(ctx: SensorContext) -> TelemetryEvent:
    return make_event(
        ctx.agent_id,
        EventKind.PROCESS_START,
        subject="winword.exe -> powershell.exe",
        data={
            "name": "powershell.exe",
            "parent": "winword.exe",
            "pid": random.randint(1000, 9000),
            "cmdline": "-EncodedCommand JABjAD0AJwBpAGUAeAA=",
        },
    )


# ---- network sensor ----

def simulated_c2_callout(ctx: SensorContext, *, domain: str = "malware-c2.example") -> TelemetryEvent:
    return make_event(
        ctx.agent_id,
        EventKind.NETWORK_CONNECT,
        subject=f"net:{domain}",
        data={
            "domain": domain,
            "ip": "203.0.113.66",
            "bytes_out": 4_500_000,
            "bytes_in": 12_000,
            "process": "edge.exe",
        },
    )


def simulated_auth_brute_force(ctx: SensorContext, *, failed_count: int = 7) -> TelemetryEvent:
    return make_event(
        ctx.agent_id,
        EventKind.AUTH_LOGIN,
        subject=f"auth:{ctx.user or 'unknown'}",
        data={
            "user": ctx.user,
            "failed_count": failed_count,
            "source_ip": "10.0.0.42",
            "result": "failure",
        },
    )


# ---- DLP scanner ----

def simulated_dlp_match(ctx: SensorContext, *, label: str = "confidential") -> TelemetryEvent:
    sample = f"label={label}|owner={ctx.user}|ts={utc_now_iso()}".encode("utf-8")
    return make_event(
        ctx.agent_id,
        EventKind.DLP_MATCH,
        subject="dlp:document",
        data={
            "label": label,
            "document_id": hashlib.sha256(sample).hexdigest()[:16],
            "channel": "email.outbound",
        },
    )


# ---- screen / clipboard sensors ----

def simulated_clipboard_secret(ctx: SensorContext, *, category: str = "credit_card") -> TelemetryEvent:
    return make_event(
        ctx.agent_id,
        EventKind.CLIPBOARD_COPY,
        subject="clipboard",
        data={"category": category, "length": 19, "entropy": 4.21, "user": ctx.user},
    )


# ---- discovery ----

ALL_SIMULATORS: dict[str, callable] = {
    "usb_mass_copy": simulated_usb_mass_copy,
    "usb_attach": simulated_usb_attach,
    "office_shell": simulated_office_spawned_shell,
    "c2_callout": simulated_c2_callout,
    "auth_brute_force": simulated_auth_brute_force,
    "dlp_match": simulated_dlp_match,
    "clipboard_secret": simulated_clipboard_secret,
}


def simulator_names() -> Iterable[str]:
    return ALL_SIMULATORS.keys()

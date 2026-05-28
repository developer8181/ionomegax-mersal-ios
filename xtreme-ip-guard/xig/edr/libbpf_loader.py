# Copyright (c) 2009–2026 Extreme Technology Company, Ramallah, Palestine.

"""Optional libbpf integration — uses ctypes when libbpf.so is present."""

from __future__ import annotations

import ctypes
import ctypes.util
import os
from typing import Any


def libbpf_available() -> bool:
    if os.environ.get("MERSAL_LIBBPF", "").strip().lower() in {"0", "false", "no"}:
        return False
    return ctypes.util.find_library("bpf") is not None


def collect_libbpf_status() -> dict[str, Any]:
    if not libbpf_available():
        return {"available": False, "engine": "libbpf"}
    try:
        lib = ctypes.CDLL(ctypes.util.find_library("bpf"))
        version_fn = getattr(lib, "libbpf_version_string", None)
        version = ""
        if version_fn:
            version_fn.restype = ctypes.c_char_p
            raw = version_fn()
            version = raw.decode() if raw else ""
        return {
            "available": True,
            "engine": "libbpf",
            "version": version,
            "note": "Use with bpftool-backed ebpf_edr for full telemetry",
        }
    except OSError as exc:
        return {"available": False, "engine": "libbpf", "error": str(exc)}

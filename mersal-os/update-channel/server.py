#!/usr/bin/env python3
"""Mersal Update Orbit — local update manifest server for lab trials."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest.json"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/manifest.json"}:
            body = MANIFEST.read_text(encoding="utf-8") if MANIFEST.is_file() else "{}"
            data = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    port = int(os.environ.get("MERSAL_UPDATE_PORT", "8091"))
    if not MANIFEST.is_file():
        MANIFEST.write_text((ROOT / "manifest.example.json").read_text(encoding="utf-8"), encoding="utf-8")
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Mersal Update Orbit at http://0.0.0.0:{port}/manifest.json")
    server.serve_forever()


if __name__ == "__main__":
    main()

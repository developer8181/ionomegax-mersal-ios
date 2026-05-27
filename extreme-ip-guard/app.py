"""Convenience entry point for the Extreme IP Guard reference build."""

from __future__ import annotations

import argparse
import os

from xig.server import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Extreme IP Guard control plane")
    parser.add_argument("--host", default=os.environ.get("XIG_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("XIG_PORT", "8090")))
    args = parser.parse_args()
    run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

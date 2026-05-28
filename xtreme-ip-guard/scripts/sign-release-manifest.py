#!/usr/bin/env python3
"""Sign a release artifact manifest (ISO, agent bundle) for Mersal supply chain."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sign Mersal release manifest")
    parser.add_argument("artifact", type=Path, help="Path to ISO or binary artifact")
    parser.add_argument("--component", default="iso", help="Component name")
    parser.add_argument("--version", required=True, help="Release version e.g. 8.6.0")
    parser.add_argument("--url", default="", help="Public download URL")
    args = parser.parse_args()

    key = os.environ.get("MERSAL_UPDATE_SIGNING_KEY", "").strip()
    if not key:
        print("Set MERSAL_UPDATE_SIGNING_KEY", file=sys.stderr)
        sys.exit(1)
    if not args.artifact.is_file():
        print(f"Artifact not found: {args.artifact}", file=sys.stderr)
        sys.exit(1)

    checksum = sha256_file(args.artifact)
    manifest_id = f"rel-{args.version.replace('.', '')}"
    body = {
        "manifest_id": manifest_id,
        "component": args.component,
        "version": args.version,
        "artifact_url": args.url or f"file://{args.artifact.resolve()}",
        "checksum_sha256": checksum,
        "artifact_size": args.artifact.stat().st_size,
        "artifact_name": args.artifact.name,
    }
    canonical = json.dumps(
        {k: body[k] for k in ("manifest_id", "component", "version", "artifact_url", "checksum_sha256")},
        sort_keys=True,
    )
    body["signature"] = hmac.new(key.encode(), canonical.encode(), hashlib.sha256).hexdigest()
    out = args.artifact.with_suffix(args.artifact.suffix + ".manifest.json")
    out.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()

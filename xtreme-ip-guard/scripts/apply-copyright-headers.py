#!/usr/bin/env python3
"""Prepend standard copyright header to Python sources (idempotent)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from xig.credits import SOURCE_HEADER  # noqa: E402

MARKER = "Extreme Technology Company, Ramallah"


def process(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if MARKER in text.split("\n", 3)[0] or MARKER in text.split("\n", 5)[2:6]:
        return False
    if text.startswith("#!"):
        first_nl = text.index("\n") + 1
        path.write_text(text[:first_nl] + SOURCE_HEADER + text[first_nl:], encoding="utf-8")
        return True
    path.write_text(SOURCE_HEADER + text, encoding="utf-8")
    return True


def main() -> None:
    count = 0
    for pattern in ("xig/**/*.py", "tests/**/*.py", "*.py", "scripts/**/*.py"):
        for path in ROOT.glob(pattern):
            if path.name == "apply-copyright-headers.py":
                continue
            if process(path):
                count += 1
                print(f"  + {path.relative_to(ROOT)}")
    print(f"Updated {count} files.")


if __name__ == "__main__":
    main()

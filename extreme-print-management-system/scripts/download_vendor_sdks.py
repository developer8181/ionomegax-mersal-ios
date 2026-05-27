#!/usr/bin/env python3
"""Vendor SDK download assistant.

Official MFP SDKs are proprietary and require manufacturer partner accounts.
This script:
  1) Documents official portal URLs for each vendor.
  2) Builds Extreme *development* bridge JARs (our code, not vendor SDKs).
  3) Creates clearly labeled stub SDK placeholders when official JARs are missing.
  4) Optionally imports JARs the user placed in sdk/jars/incoming/

It does NOT bypass login walls or redistribute copyrighted vendor SDK binaries.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK_ROOT = ROOT / "sdk"
JAR_DIR = SDK_ROOT / "jars"
INCOMING = JAR_DIR / "incoming"
PORTALS = Path(__file__).resolve().parent / "vendor_sdk_portals.json"
JAVA_SRC = SDK_ROOT / "java"

STUB_NOTICE = textwrap.dedent(
    """
    EXTREME PRINT — DEVELOPMENT STUB ONLY
    This is NOT an official manufacturer SDK.
    Download the real SDK from the vendor partner portal and replace this file.
    """
).strip()


def load_portals() -> dict:
    return json.loads(PORTALS.read_text(encoding="utf-8"))


def compile_java(out_dir: Path) -> None:
    sources = sorted(JAVA_SRC.rglob("*.java"))
    if not sources:
        raise FileNotFoundError(f"No Java sources under {JAVA_SRC}")
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = ["javac", "-d", str(out_dir), *[str(s) for s in sources]]
    subprocess.run(cmd, check=True)


def jar_create(jar_path: Path, base_dir: Path, extra_meta: dict[str, str] | None = None) -> None:
    jar_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(jar_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(base_dir.rglob("*")):
            if file.is_file():
                arc = file.relative_to(base_dir).as_posix()
                zf.write(file, arc)
        if extra_meta:
            for name, value in extra_meta.items():
                zf.writestr(name, value)


def build_extreme_bridge_jars(build_dir: Path) -> list[Path]:
    compile_java(build_dir / "classes")
    classes = build_dir / "classes"
    created: list[Path] = []
    mapping = {
        "extreme-servlet.jar": ["com/extreme/epms/ExtremeSdkServlet.class"],
        "hp-bridge.jar": ["com/extreme/epms/hp/HPExtremeBridge.class", "com/extreme/epms/ExtremeSdkServlet.class"],
        "canon-bridge.jar": ["com/extreme/epms/canon/CanonExtremeBridge.class", "com/extreme/epms/ExtremeSdkServlet.class"],
        "ricoh-bridge.jar": ["com/extreme/epms/ricoh/RicohExtremeBridge.class", "com/extreme/epms/ExtremeSdkServlet.class"],
        "xerox-bridge.jar": ["com/extreme/epms/xerox/XeroxExtremeBridge.class", "com/extreme/epms/ExtremeSdkServlet.class"],
        "konica-minolta-bridge.jar": [
            "com/extreme/epms/konica/KonicaExtremeBridge.class",
            "com/extreme/epms/ExtremeSdkServlet.class",
        ],
        "kyocera-bridge.jar": ["com/extreme/epms/kyocera/KyoceraExtremeBridge.class", "com/extreme/epms/ExtremeSdkServlet.class"],
        "lexmark-bridge.jar": ["com/extreme/epms/lexmark/LexmarkExtremeBridge.class", "com/extreme/epms/ExtremeSdkServlet.class"],
        "olivetti-bridge.jar": ["com/extreme/epms/olivetti/OlivettiExtremeBridge.class", "com/extreme/epms/ExtremeSdkServlet.class"],
    }
    for jar_name, _ in mapping.items():
        jar_path = JAR_DIR / jar_name
        jar_create(jar_path, classes, {"META-INF/EXTREME-NOTICE.txt": f"Extreme bridge: {jar_name}\n"})
        created.append(jar_path)
    return created


def create_stub_sdk_jar(vendor: str, jar_name: str) -> Path:
    """Placeholder until user drops official SDK in sdk/jars/incoming/."""
    jar_path = JAR_DIR / jar_name
    official = INCOMING / jar_name
    if official.exists():
        shutil.copy2(official, jar_path)
        return jar_path
    if jar_path.exists() and jar_path.stat().st_size > 800:
        try:
            with zipfile.ZipFile(jar_path) as zf:
                if "META-INF/EXTREME-STUB.txt" not in zf.namelist():
                    return jar_path
        except zipfile.BadZipFile:
            pass
    pkg = vendor.replace("-", "")
    stub_root = Path(__file__).resolve().parent / "_stub_build" / vendor
    if stub_root.exists():
        shutil.rmtree(stub_root)
    java_file = stub_root / "src" / "StubSdk.java"
    java_file.parent.mkdir(parents=True)
    java_file.write_text(
        f"package com.extreme.epms.stub.{pkg};\n"
        f"public final class StubSdk {{\n"
        f"  private StubSdk() {{}}\n"
        f"  public static String vendor() {{ return \"{vendor}\"; }}\n"
        f"}}\n",
        encoding="utf-8",
    )
    classes = stub_root / "classes"
    subprocess.run(
        ["javac", "-d", str(classes), str(java_file)],
        check=True,
        capture_output=True,
    )
    jar_create(
        jar_path,
        classes,
        {
            "META-INF/EXTREME-STUB.txt": STUB_NOTICE + f"\nVendor: {vendor}\n",
            "META-INF/MANIFEST.MF": f"Implementation-Title: Extreme-Stub-{vendor}\n",
        },
    )
    return jar_path


def import_incoming(overwrite: bool = False) -> list[Path]:
    imported: list[Path] = []
    if not INCOMING.exists():
        INCOMING.mkdir(parents=True)
        return imported
    for src in INCOMING.glob("*.jar"):
        dest = JAR_DIR / src.name
        if dest.exists() and not overwrite:
            continue
        shutil.copy2(src, dest)
        imported.append(dest)
    return imported


def print_portal_report(portals: dict) -> None:
    print("\n=== Official vendor SDK portals (manual download required) ===\n")
    for vendor, info in portals.items():
        print(f"[{vendor}] {info['name']} — access: {info['access']}")
        print(f"  Portal: {info['portal']}")
        for page in info.get("sdk_pages", []):
            if page:
                print(f"  Page:   {page}")
        print(f"  Expected files: {', '.join(info['expected_jars'])}")
        print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vendor SDK download assistant for Extreme Print")
    parser.add_argument("--build-bridges", action="store_true", help="Compile Extreme Java bridge JARs")
    parser.add_argument("--create-stubs", action="store_true", help="Create development stub SDK JARs")
    parser.add_argument("--import-incoming", action="store_true", help="Copy sdk/jars/incoming/*.jar into sdk/jars/")
    parser.add_argument("--list-portals", action="store_true", help="Show official download portals")
    parser.add_argument("--all", action="store_true", help="Run build-bridges, create-stubs, import-incoming, list-portals")
    args = parser.parse_args(argv)

    if not any([args.build_bridges, args.create_stubs, args.import_incoming, args.list_portals, args.all]):
        args.all = True

    portals = load_portals()
    JAR_DIR.mkdir(parents=True, exist_ok=True)
    INCOMING.mkdir(parents=True, exist_ok=True)

    if args.list_portals or args.all:
        print_portal_report(portals)
        print(
            "Place JARs you download manually into:\n"
            f"  {INCOMING}\n"
            "Then run: python3 scripts/download_vendor_sdks.py --import-incoming\n"
        )

    if args.build_bridges or args.all:
        try:
            built = build_extreme_bridge_jars(Path(__file__).resolve().parent / "_java_build")
            print(f"Built {len(built)} Extreme bridge JAR(s) in {JAR_DIR}")
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            print(f"Java build skipped or failed: {exc}", file=sys.stderr)
            print("Install JDK (javac) to build bridge JARs.", file=sys.stderr)

    if args.create_stubs or args.all:
        stub_names = {
            "hp": "oxp-sdk.jar",
            "canon": "meap-sdk.jar",
            "ricoh": "smartsdk.jar",
            "xerox": "eip-sdk.jar",
            "konica-minolta": "openapi-sdk.jar",
            "kyocera": "hypas-sdk.jar",
            "lexmark": "esf-sdk.jar",
            "olivetti": "olivetti-connect-sdk.jar",
        }
        for vendor, jar_name in stub_names.items():
            path = create_stub_sdk_jar(vendor, jar_name)
            print(f"Stub SDK: {path.name} ({path.stat().st_size} bytes) [NOT official]")

    if args.import_incoming or args.all:
        copied = import_incoming()
        if copied:
            print(f"Imported {len(copied)} official JAR(s) from incoming/")
        else:
            print(f"No new JARs in {INCOMING}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

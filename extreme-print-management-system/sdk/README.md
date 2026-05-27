# Extreme Print — Vendor SDK Integration Pack

This directory contains **Java bridge projects** and **JAR placement** for on-device deployment on each MFD platform.

## Layout

```text
sdk/
  jars/              # Place vendor SDK JARs here (not committed)
  java/
    extreme-servlet/ # Universal REST servlet (all vendors)
    hp/              # HP OXP / Workpath bridge
    canon/           # Canon MEAP bridge
    ricoh/           # Ricoh SmartSDK bridge
    xerox/           # Xerox EIP bridge
    konica/          # Konica Minolta OpenAPI bridge
    kyocera/         # Kyocera HyPAS bridge
    lexmark/         # Lexmark eSF bridge
    olivetti/        # Olivetti Connect bridge
```

## Python device clients

Runtime HTTP clients live in `epms/embedded/sdk_clients/`. Each vendor:

1. Calls **Extreme servlet** at `{device}/extreme/sdk/v1/*` when deployed.
2. Falls back to **vendor-native HTTP/XML** paths documented in `vendor_impl.py`.

## Deploy on device

1. Download the official SDK from the vendor (requires partner account).
2. Copy JARs into `sdk/jars/` (see `sdk/jars/README.md`).
3. Build the matching `sdk/java/<vendor>/` project with vendor toolchain.
4. Install the Extreme servlet + bridge on the MFD.
5. Set `device_address` to `https://<mfd-ip>/` in Printer Controller.

## Build (example)

```bash
cd sdk/java/extreme-servlet
# Use vendor IDE (Eclipse MEAP, HP Workpath SDK, etc.)
```

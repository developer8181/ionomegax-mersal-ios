# Vendor SDK JARs (not included in git)

## Automated assistant

```bash
python3 scripts/download_vendor_sdks.py --all
```

This builds Extreme `*-bridge.jar` files and development stubs. **Official vendor SDKs** must be downloaded from manufacturer portals (login required) and placed in `sdk/jars/incoming/`.

See `docs/SDK_DOWNLOAD_AR.md` and `scripts/vendor_sdk_portals.json`.

## Manual placement

Place official manufacturer SDK files here before building Java bridges:

| Vendor | Typical JAR names (examples) |
| --- | --- |
| HP | `oxp-sdk.jar`, `workpath-sdk.jar` |
| Canon | `meap-sdk.jar` |
| Ricoh | `smartsdk.jar` |
| Xerox | `eip-sdk.jar` |
| Konica Minolta | `openapi-sdk.jar` |
| Kyocera | `hypas-sdk.jar` |
| Lexmark | `esf-sdk.jar` |
| Olivetti | `olivetti-connect-sdk.jar` |

Files in this folder are gitignored except this README.

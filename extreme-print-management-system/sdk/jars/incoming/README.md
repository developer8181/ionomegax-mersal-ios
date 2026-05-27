# Incoming official vendor SDK JARs

1. Log in to each manufacturer's developer portal (see `scripts/vendor_sdk_portals.json`).
2. Download the SDK JAR/WAR files you are licensed to use.
3. Copy them here with the expected names, for example:
   - `oxp-sdk.jar`
   - `meap-sdk.jar`
   - `smartsdk.jar`
   - `eip-sdk.jar`
   - `openapi-sdk.jar`
   - `hypas-sdk.jar`
   - `esf-sdk.jar`
   - `olivetti-connect-sdk.jar`
4. Run:

```bash
python3 scripts/download_vendor_sdks.py --import-incoming
```

Official JARs overwrite development stubs in the parent `sdk/jars/` folder.

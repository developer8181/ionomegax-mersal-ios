#!/usr/bin/env bash
set -euo pipefail
LABEL="com.ionomegax.mersal-guard.agent"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PLIST="/Library/LaunchDaemons/${LABEL}.plist"
sudo tee "${PLIST}" >/dev/null <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>${ROOT}/agent.py</string>
    <string>daemon</string>
    <string>--config</string>
    <string>/etc/mersal-guard/agent.json</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
EOF
sudo launchctl load -w "${PLIST}"
echo "Mersal Guard macOS agent installed (${LABEL})"

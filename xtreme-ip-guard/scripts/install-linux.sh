#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${MERSAL_PREFIX:-/opt/mersal-guard}"
CONFIG_DIR="${MERSAL_CONFIG_DIR:-/etc/mersal-guard}"
DATA_DIR="${MERSAL_DATA_DIR:-/var/lib/mersal-guard}"

echo "Installing Ionomegax Mersal Guard to ${PREFIX}"

sudo mkdir -p "${PREFIX}" "${CONFIG_DIR}" "${DATA_DIR}"
sudo cp -r "${ROOT}/app.py" "${ROOT}/agent.py" "${ROOT}/xig" "${ROOT}/web" "${PREFIX}/"
sudo cp "${ROOT}/config/agent.json" "${CONFIG_DIR}/agent.json"
sudo cp "${ROOT}/deploy/linux/"*.service /etc/systemd/system/

if ! id mersal >/dev/null 2>&1; then
  sudo useradd --system --home "${DATA_DIR}" --shell /usr/sbin/nologin mersal || true
fi
sudo chown -R mersal:mersal "${DATA_DIR}"

echo "Enable services:"
echo "  sudo systemctl daemon-reload"
echo "  sudo systemctl enable --now mersal-guard-server"
echo "  sudo systemctl enable --now mersal-guard-agent"
echo "Console: http://$(hostname -I | awk '{print $1}'):8090/console/"

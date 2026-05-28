#!/usr/bin/env bash
# Ionomegax Mersal Guard — production trial install (Linux)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PREFIX="${MERSAL_PREFIX:-/opt/mersal-guard}"
CONFIG_DIR="${MERSAL_CONFIG_DIR:-/etc/mersal-guard}"
DATA_DIR="${MERSAL_DATA_DIR:-/var/lib/mersal-guard}"
TLS_DIR="${MERSAL_TLS_DIR:-${CONFIG_DIR}/tls}"

echo "=== Mersal Guard Production Install v3.0 ==="

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo $0"
  exit 1
fi

bash "${ROOT}/scripts/install-linux.sh"

mkdir -p "${TLS_DIR}" "${DATA_DIR}"
if [[ ! -f "${TLS_DIR}/server.crt" ]]; then
  echo "Generating TLS certificates..."
  MERSAL_TLS_DIR="${TLS_DIR}" bash "${ROOT}/scripts/generate-tls.sh"
fi

ENV_FILE="${CONFIG_DIR}/mersal-production.env"
cat >"${ENV_FILE}" <<EOF
MERSAL_PRODUCTION=1
MERSAL_HOST=0.0.0.0
MERSAL_PORT=8090
MERSAL_DB=${DATA_DIR}/mersal-guard.sqlite3
MERSAL_TLS_CERT=${TLS_DIR}/server.crt
MERSAL_TLS_KEY=${TLS_DIR}/server.key
MERSAL_ADMIN_USER=${MERSAL_ADMIN_USER:-admin}
MERSAL_ADMIN_PASSWORD=${MERSAL_ADMIN_PASSWORD:-$(openssl rand -hex 12)}
MERSAL_API_TOKEN=${MERSAL_API_TOKEN:-$(openssl rand -hex 24)}
MERSAL_BOOTSTRAP=1
MERSAL_KEV_FEED_URL=https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
EOF
chmod 600 "${ENV_FILE}"

mkdir -p /etc/systemd/system/mersal-guard-server.service.d
cat >/etc/systemd/system/mersal-guard-server.service.d/production.conf <<EOF
[Service]
EnvironmentFile=${ENV_FILE}
EOF

systemctl daemon-reload
systemctl enable --now mersal-guard-server
sleep 3

IP="$(hostname -I 2>/dev/null | awk '{print $1}' || echo 127.0.0.1)"
echo ""
echo "Production server started."
echo "  Command Center: https://${IP}:8090/console/"
echo "  Readiness API:  https://${IP}:8090/api/system/readiness"
echo "  Credentials:    ${ENV_FILE}"
echo ""
echo "Install endpoint agent: sudo systemctl enable --now mersal-guard-agent"

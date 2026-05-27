#!/usr/bin/env bash
# Install Extreme Print Management System on a Linux VPS (Ubuntu/Debian).
#
# Usage (on your VPS as root or with sudo):
#   curl -fsSL .../install_on_vps.sh -o install_on_vps.sh   # or clone repo
#   sudo bash install_on_vps.sh --domain print.example.com --email you@example.com
#
# Options:
#   --method docker|native     (default: docker)
#   --domain NAME              Public hostname for Nginx (optional)
#   --email ADDR               Let's Encrypt email (needs --domain)
#   --port PORT                Public HTTP port before SSL (default: 80)
#   --install-dir PATH         Install root (default: /opt/epms)
#   --skip-nginx               Do not configure Nginx
#   --seed-demo                Load enterprise demo data after install
#
set -euo pipefail

METHOD="docker"
DOMAIN=""
EMAIL=""
HTTP_PORT="80"
INSTALL_DIR="/opt/epms"
SKIP_NGINX=0
SEED_DEMO=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --method) METHOD="$2"; shift 2 ;;
    --domain) DOMAIN="$2"; shift 2 ;;
    --email) EMAIL="$2"; shift 2 ;;
    --port) HTTP_PORT="$2"; shift 2 ;;
    --install-dir) INSTALL_DIR="$2"; shift 2 ;;
    --skip-nginx) SKIP_NGINX=1; shift ;;
    --seed-demo) SEED_DEMO=1; shift ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash $0 ..." >&2
  exit 1
fi

if [[ -n "$EMAIL" && -z "$DOMAIN" ]]; then
  echo "--email requires --domain" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq curl git ca-certificates python3 python3-venv openssl

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_NAME="extreme-print-management-system"
TARGET="$INSTALL_DIR/$APP_NAME"

mkdir -p "$INSTALL_DIR"
if [[ "$ROOT" != "$TARGET" ]]; then
  rm -rf "$TARGET"
  mkdir -p "$(dirname "$TARGET")"
  cp -a "$ROOT" "$TARGET"
fi
cd "$TARGET"

bash scripts/provision_production.sh
ENV_FILE="$TARGET/deploy/production.generated.env"

if [[ "$SEED_DEMO" -eq 1 ]]; then
  if grep -q '^EPMS_SEED_DEMO=' "$ENV_FILE"; then
    sed -i 's/^EPMS_SEED_DEMO=.*/EPMS_SEED_DEMO=1/' "$ENV_FILE"
  else
    echo "EPMS_SEED_DEMO=1" >>"$ENV_FILE"
  fi
fi

ADMIN_PASS="$(grep '^EPMS_BOOTSTRAP_ADMIN_PASSWORD=' "$ENV_FILE" | cut -d= -f2-)"

install_docker() {
  if command -v docker >/dev/null 2>&1; then
    return
  fi
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
}

write_nginx() {
  [[ "$SKIP_NGINX" -eq 1 || -z "$DOMAIN" ]] && return
  apt-get install -y -qq nginx
  local conf="/etc/nginx/sites-available/epms"
  sed "s/EPMS_DOMAIN/$DOMAIN/g; s/127.0.0.1:8080/127.0.0.1:8080/" "$TARGET/deploy/nginx/epms.conf.example" >"$conf"
  ln -sf "$conf" /etc/nginx/sites-enabled/epms
  rm -f /etc/nginx/sites-enabled/default
  nginx -t
  systemctl enable --now nginx
  systemctl reload nginx
}

write_systemd_native() {
  id -u epms &>/dev/null || useradd --system --home "$INSTALL_DIR" --shell /usr/sbin/nologin epms
  chown -R epms:epms "$INSTALL_DIR"
  install -m 600 "$ENV_FILE" /etc/epms/production.env
  sed -e "s|/opt/epms/extreme-print-management-system|$TARGET|g" \
      -e 's|app\.py|app_production.py|' \
      "$TARGET/deploy/epms.service" >/etc/systemd/system/epms.service
  systemctl daemon-reload
  systemctl enable --now epms
}

install_docker_stack() {
  install_docker
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
  export EPMS_SESSION_SECRET EPMS_AGENT_TOKEN EPMS_BOOTSTRAP_ADMIN_PASSWORD
  docker compose -f deploy/docker-compose.production.yml up --build -d
}

write_credentials() {
  local url="http://$(curl -fsS ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}'):8080"
  [[ -n "$DOMAIN" ]] && url="https://$DOMAIN"
  cat >"$INSTALL_DIR/CREDENTIALS.txt" <<EOF
Extreme Print Management System — VPS install summary
====================================================
Web UI:        $url/
Release:       $url/release
Health:        $url/api/health
Admin user:    admin
Admin pass:    $ADMIN_PASS
Env file:      $ENV_FILE
Docker:        docker compose -f $TARGET/deploy/docker-compose.production.yml ps
Logs:          journalctl -u epms -f   OR   docker compose -f $TARGET/deploy/docker-compose.production.yml logs -f

Change the admin password after first login. Store this file securely and delete when done.
EOF
  chmod 600 "$INSTALL_DIR/CREDENTIALS.txt"
}

case "$METHOD" in
  docker)
    install_docker_stack
    ;;
  native)
  write_systemd_native
    ;;
  *)
    echo "Unknown method: $METHOD (use docker or native)" >&2
    exit 1
    ;;
esac

write_nginx

if [[ -n "$DOMAIN" && -n "$EMAIL" ]]; then
  apt-get install -y -qq certbot python3-certbot-nginx
  certbot --nginx -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive --redirect || true
fi

write_credentials

echo ""
echo "=============================================="
echo " EPMS installed on this VPS"
echo "=============================================="
cat "$INSTALL_DIR/CREDENTIALS.txt"
echo "=============================================="

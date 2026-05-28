#!/usr/bin/env bash
# Generate self-signed CA, server, and agent certificates for Mersal mTLS trial.
set -euo pipefail

TLS_DIR="${MERSAL_TLS_DIR:-$(cd "$(dirname "$0")/.." && pwd)/data/tls}"
DAYS="${MERSAL_TLS_DAYS:-825}"
CN_SERVER="${MERSAL_TLS_SERVER_CN:-mersal-guard.local}"

mkdir -p "${TLS_DIR}"
cd "${TLS_DIR}"

if [[ -f ca.crt && -f server.crt && -f agent.crt ]]; then
  echo "TLS assets already exist in ${TLS_DIR}"
  exit 0
fi

openssl req -x509 -newkey rsa:4096 -sha256 -days "${DAYS}" -nodes \
  -keyout ca.key -out ca.crt \
  -subj "/CN=Mersal Guard CA/O=Extreme Technology/C=PS"

openssl req -newkey rsa:4096 -nodes -keyout server.key -out server.csr \
  -subj "/CN=${CN_SERVER}/O=Extreme Technology/C=PS"

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days "${DAYS}" -sha256

openssl req -newkey rsa:4096 -nodes -keyout agent.key -out agent.csr \
  -subj "/CN=mersal-agent/O=Extreme Technology/C=PS"

openssl x509 -req -in agent.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out agent.crt -days "${DAYS}" -sha256

chmod 600 ca.key server.key agent.key
rm -f server.csr agent.csr

echo "TLS generated in ${TLS_DIR}:"
echo "  ca.crt, server.crt/key, agent.crt/key"

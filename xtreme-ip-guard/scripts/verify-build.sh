#!/usr/bin/env bash
# Post-build smoke verification (no mock endpoints).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

DB="${ROOT}/data/verify-build.sqlite3"
rm -f "${DB}"
export MERSAL_DB="${DB}"
export MERSAL_PRODUCTION=1
export MERSAL_API_TOKEN=verify-build-token
export MERSAL_BOOTSTRAP=1

python3 app.py >/tmp/mersal-verify.log 2>&1 &
PID=$!
trap 'kill "${PID}" 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
  if curl -sf http://127.0.0.1:8090/api/system/about >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -sf http://127.0.0.1:8090/api/system/about | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d.get('version','').startswith('3.1'), d
print('about:', d.get('version'))
"

curl -sf http://127.0.0.1:8090/api/system/build | python3 -c "
import json,sys
d=json.load(sys.stdin)
assert d.get('version'), d
print('build:', d.get('version'), d.get('git_commit'))
"

curl -sf http://127.0.0.1:8090/api/system/readiness | python3 -c "
import json,sys
r=json.load(sys.stdin)
assert 'checks' in r
print('readiness checks:', len(r['checks']))
"

echo "verify-build: OK"

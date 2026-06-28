#!/bin/bash
# Ждём готовности backend после рестарта (локально на VPS).
set -euo pipefail

URL="${1:-http://127.0.0.1:8088/health}"
MAX="${WAIT_HEALTH_SECONDS:-120}"
i=0
while [ "$i" -lt "$MAX" ]; do
  if curl -fsS --max-time 5 "$URL" | grep -q '"status"'; then
    echo "Health OK: $URL"
    exit 0
  fi
  sleep 2
  i=$((i + 2))
done
echo "FAIL: backend not healthy after ${MAX}s ($URL)" >&2
exit 1

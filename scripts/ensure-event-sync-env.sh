#!/usr/bin/env bash
# Idempotent: ensure EVENT_SYNC_INTERVAL_HOURS=4 in VPS .env when unset or legacy 0/12.
set -euo pipefail

ENV_FILE="${1:-/opt/pgbot/.env}"
KEY="EVENT_SYNC_INTERVAL_HOURS"
DESIRED="4"

[ -f "$ENV_FILE" ] || exit 0

if grep -q "^${KEY}=" "$ENV_FILE"; then
  current="$(grep -E "^${KEY}=" "$ENV_FILE" | tail -1 | cut -d= -f2- | tr -d '\r"'"'"' ')"
  if [ "$current" = "0" ] || [ "$current" = "12" ]; then
    sed -i "s/^${KEY}=.*/${KEY}=${DESIRED}/" "$ENV_FILE"
    echo "Updated ${KEY}=${DESIRED} in ${ENV_FILE}"
  fi
else
  printf '\n%s=%s\n' "$KEY" "$DESIRED" >> "$ENV_FILE"
  echo "Appended ${KEY}=${DESIRED} to ${ENV_FILE}"
fi

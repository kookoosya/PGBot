#!/bin/bash
# Проверка VK-бота на проде (callback + group token). Mini App не трогаем.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=canonical-site.sh
source "$SCRIPT_DIR/canonical-site.sh"

BASE="${1:-${SMOKE_BASE_URL:-$CANONICAL_SITE_URL}}"
API="${BASE%/}/api/v1"

fail=0

info=$(curl -sS --max-time 20 "$API/public/info")
if echo "$info" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('vk_bot_ready') else 1)"; then
  echo "OK   vk_bot_ready"
else
  echo "FAIL vk_bot_ready=false"
  fail=1
fi

confirm=$(curl -sS --max-time 15 -X POST "$API/vk/callback" \
  -H "Content-Type: application/json" \
  -d '{"type":"confirmation","group_id":238536142}')
if [[ -n "$confirm" && "$confirm" != "ok" ]]; then
  echo "OK   callback confirmation ($confirm)"
else
  echo "FAIL callback confirmation"
  fail=1
fi

if [[ -f "$SCRIPT_DIR/../.deploy.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/../.deploy.env"
  set +a
fi
if [[ -n "${SSHPASS:-${VPS_PASSWORD:-}}" ]]; then
  SSHPASS_BIN=""
  if command -v sshpass >/dev/null; then SSHPASS_BIN=sshpass
  elif [[ -x /tmp/sshpass-extract/usr/bin/sshpass ]]; then SSHPASS_BIN=/tmp/sshpass-extract/usr/bin/sshpass
  fi
  if [[ -n "$SSHPASS_BIN" ]]; then
    SSHPASS="${SSHPASS:-$VPS_PASSWORD}" "$SSHPASS_BIN" -e ssh -o StrictHostKeyChecking=no "${VPS_USER:-root}@${VPS_HOST:-192.210.213.135}" \
      'cd /opt/pgbot && docker compose -f docker-compose.prod.yml exec -T backend python scripts/check_event_sources.py' \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print('INFO event_sources', d.get('status'), 'vk_groups', d.get('vk_groups_resolved'))"
  fi
fi

exit "$fail"

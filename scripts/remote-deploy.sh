#!/bin/bash
# Деплой на VPS. Требует SSHPASS или SSH-ключ в агенте.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.deploy.env" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/../.deploy.env"
  set +a
fi

HOST="${VPS_HOST:-192.210.213.135}"
USER="${VPS_USER:-root}"
BRANCH="${BRANCH:-main}"

SSHPASS_BIN=""
if command -v sshpass >/dev/null; then
  SSHPASS_BIN="sshpass"
elif [ -x /tmp/sshpass-extract/usr/bin/sshpass ]; then
  SSHPASS_BIN="/tmp/sshpass-extract/usr/bin/sshpass"
fi

# Синхронизируем API-ключи из .deploy.env до перезапуска контейнеров
bash "$SCRIPT_DIR/sync-vps-env.sh" 2>/dev/null || true

REMOTE="set -e
cd /opt/pgbot
git fetch origin $BRANCH
git checkout $BRANCH
git pull origin $BRANCH
bash scripts/vps-sync-ai-keys.sh 2>/dev/null || true
bash scripts/setup-russia-mirror.sh
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head
docker compose -f docker-compose.prod.yml exec -T backend python scripts/seed_events.py 2>/dev/null || true
echo Deploy OK: https://192-210-213-135.sslip.io"

export SSHPASS="${SSHPASS:-${VPS_PASSWORD:-}}"

if [ -n "${SSHPASS:-}" ] && [ -n "$SSHPASS_BIN" ]; then
  unset SSH_ASKPASS SSH_ASKPASS_REQUIRE DISPLAY
  SSHPASS="$SSHPASS" "$SSHPASS_BIN" -e ssh -o StrictHostKeyChecking=no "$USER@$HOST" "$REMOTE"
elif [ -n "${VPS_SSH_KEY:-}" ]; then
  KEY_FILE="$(mktemp)"
  trap 'rm -f "$KEY_FILE"' EXIT
  printf '%s\n' "$VPS_SSH_KEY" > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
  ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no -o BatchMode=yes "$USER@$HOST" "$REMOTE"
elif [ -n "${SSH_AUTH_SOCK:-}" ] && ssh-add -l >/dev/null 2>&1; then
  ssh -o StrictHostKeyChecking=no -o BatchMode=yes "$USER@$HOST" "$REMOTE"
else
  echo "Нет доступа к VPS $USER@$HOST" >&2
  echo "Добавьте секрет VPS_PASSWORD или SSHPASS в cursor.com/dashboard/cloud-agents" >&2
  echo "или GitHub Secret VPS_PASSWORD для Actions → Deploy VPS" >&2
  exit 1
fi

echo "Deploy OK: https://pushkinskie-gory.ru"

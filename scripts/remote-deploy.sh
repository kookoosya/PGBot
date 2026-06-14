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
# Синхронизируем API-ключи из .deploy.env до перезапуска контейнеров
bash "$SCRIPT_DIR/sync-vps-env.sh" 2>/dev/null || true

REMOTE="cd /opt/pgbot && git fetch origin $BRANCH && git checkout $BRANCH && git pull origin $BRANCH && bash scripts/vps-sync-ai-keys.sh && bash scripts/setup-russia-mirror.sh && docker compose -f docker-compose.prod.yml up -d --build && docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head"

export SSHPASS="${SSHPASS:-${VPS_PASSWORD:-}}"

if [ -n "${SSHPASS:-}" ] && command -v sshpass >/dev/null; then
  unset SSH_ASKPASS SSH_ASKPASS_REQUIRE DISPLAY
  SSHPASS="$SSHPASS" sshpass -e ssh -o StrictHostKeyChecking=no "$USER@$HOST" "$REMOTE"
elif [ -n "${SSH_AUTH_SOCK:-}" ] && ssh-add -l >/dev/null 2>&1; then
  ssh -o StrictHostKeyChecking=no -o BatchMode=yes "$USER@$HOST" "$REMOTE"
else
  echo "Нет SSHPASS и нет ключа в SSH-агенте для $USER@$HOST" >&2
  exit 1
fi

echo "Deploy OK: https://pushkinskie-gory.ru"

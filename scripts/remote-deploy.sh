#!/bin/bash
# Деплой на VPS. Требует SSHPASS или SSH-ключ в агенте.
set -euo pipefail

HOST="${VPS_HOST:-192.210.213.135}"
USER="${VPS_USER:-root}"
BRANCH="${BRANCH:-cursor/narodny-kontrol-mvp-e7fb}"
REMOTE="cd /opt/pgbot && git fetch origin $BRANCH && git checkout $BRANCH && git pull origin $BRANCH && docker compose -f docker-compose.prod.yml up -d --build && docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head"

if [ -n "${SSHPASS:-}" ] && command -v sshpass >/dev/null; then
  SSHPASS="$SSHPASS" sshpass -e ssh -o StrictHostKeyChecking=no "$USER@$HOST" "$REMOTE"
elif [ -n "${SSH_AUTH_SOCK:-}" ] && ssh-add -l >/dev/null 2>&1; then
  ssh -o StrictHostKeyChecking=no -o BatchMode=yes "$USER@$HOST" "$REMOTE"
else
  echo "Нет SSHPASS и нет ключа в SSH-агенте для $USER@$HOST" >&2
  exit 1
fi

echo "Deploy OK: https://pushkiny.gmxreply.com"

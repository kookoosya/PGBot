#!/bin/bash
# Деплой на VPS. Требует SSHPASS или SSH-ключ в агенте.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=canonical-site.sh
source "$SCRIPT_DIR/canonical-site.sh"

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

bash "$SCRIPT_DIR/sync-vps-env.sh" 2>/dev/null || true

REMOTE="set -e
cd /opt/pgbot
git fetch origin $BRANCH
git checkout $BRANCH
git pull origin $BRANCH
bash scripts/vps-deploy.sh"

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
  echo "Добавьте VPS_PASSWORD в GitHub Secrets или .deploy.env" >&2
  exit 1
fi

echo "Deploy OK: $CANONICAL_SITE_URL"

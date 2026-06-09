#!/bin/bash
# Синхронизация секретов из .deploy.env → /opt/pgbot/.env на VPS
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
REMOTE_ENV="/opt/pgbot/.env"
export SSHPASS="${SSHPASS:-${VPS_PASSWORD:-}}"

_ssh() {
  if [ -n "${SSHPASS:-}" ] && command -v sshpass >/dev/null; then
    unset SSH_ASKPASS SSH_ASKPASS_REQUIRE DISPLAY
    SSHPASS="$SSHPASS" sshpass -e ssh -o StrictHostKeyChecking=no "$USER@$HOST" "$@"
  else
    ssh -o StrictHostKeyChecking=no -o BatchMode=yes "$USER@$HOST" "$@"
  fi
}

_set_env_var() {
  local name="$1"
  local value="$2"
  [ -n "$value" ] || return 0
  local b64
  b64=$(printf '%s' "$value" | base64 -w0 2>/dev/null || printf '%s' "$value" | base64)
  _ssh "python3 -c \"
import re, base64
from pathlib import Path
name = '$name'
val = base64.b64decode('$b64').decode('utf-8')
path = Path('$REMOTE_ENV')
text = path.read_text(encoding='utf-8') if path.is_file() else ''
pat = r'^' + re.escape(name) + r'=.*$'
if re.search(pat, text, flags=re.M):
    text = re.sub(pat, name + '=' + val, text, flags=re.M)
else:
    if text and not text.endswith(chr(10)):
        text += chr(10)
    text += name + '=' + val + chr(10)
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(text, encoding='utf-8')
print('set', name)
\""
}

_set_env_var POLLINATIONS_API_KEY "${POLLINATIONS_API_KEY:-}"
_set_env_var OPENROUTER_API_KEY "${OPENROUTER_API_KEY:-}"
_set_env_var OPENAI_API_KEY "${OPENAI_API_KEY:-}"
_set_env_var PERPLEXITY_API_KEY "${PERPLEXITY_API_KEY:-}"
_set_env_var AI_HTTP_PROXY "${AI_HTTP_PROXY:-}"
_set_env_var AI_HTTPS_PROXY "${AI_HTTPS_PROXY:-}"
_set_env_var AI_FREE_DAILY_LIMIT "${AI_FREE_DAILY_LIMIT:-10}"
_set_env_var AI_TRIAL_DAILY_LIMIT "${AI_TRIAL_DAILY_LIMIT:-50}"
_set_env_var AI_PRO_DAILY_LIMIT "${AI_PRO_DAILY_LIMIT:-150}"
_set_env_var AI_MAX_DAILY_LIMIT "${AI_MAX_DAILY_LIMIT:-150}"
_set_env_var AI_PRO_PRICE "${AI_PRO_PRICE:-299}"
_set_env_var YOOKASSA_SHOP_ID "${YOOKASSA_SHOP_ID:-}"
_set_env_var YOOKASSA_SECRET_KEY "${YOOKASSA_SECRET_KEY:-}"
_set_env_var YOOKASSA_RETURN_URL "${YOOKASSA_RETURN_URL:-https://192-210-213-135.sslip.io/ai?paid=1}"
_set_env_var GEMINI_API_KEY "${GEMINI_API_KEY:-}"
_set_env_var KINOPOISK_API_TOKEN "${KINOPOISK_API_TOKEN:-}"
_set_env_var VK_GROUP_TOKEN "${VK_GROUP_TOKEN:-}"
_set_env_var VK_CONFIRMATION_CODE "${VK_CONFIRMATION_CODE:-}"
_set_env_var VK_SECRET_KEY "${VK_SECRET_KEY:-}"
_set_env_var VK_GROUP_ID "${VK_GROUP_ID:-}"
_set_env_var VK_GROUP_URL "${VK_GROUP_URL:-}"
_set_env_var VK_WALL_POST_ENABLED "${VK_WALL_POST_ENABLED:-0}"
_set_env_var VK_USER_TOKEN "${VK_USER_TOKEN:-}"

echo "Env sync OK on $HOST"

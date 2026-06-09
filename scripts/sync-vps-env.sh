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
_set_env_var GEMINI_API_KEY "${GEMINI_API_KEY:-}"
_set_env_var KINOPOISK_API_TOKEN "${KINOPOISK_API_TOKEN:-}"

echo "Env sync OK on $HOST"

#!/bin/bash
# Подтянуть секреты с VPS → локальный .deploy.env (файл в .gitignore).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCAL_ENV="$SCRIPT_DIR/../.deploy.env"
REMOTE_ENV="/opt/pgbot/.env"

if [ -f "$LOCAL_ENV" ]; then
  set -a
  # shellcheck source=/dev/null
  source "$LOCAL_ENV"
  set +a
fi

HOST="${VPS_HOST:-192.210.213.135}"
USER="${VPS_USER:-root}"
export SSHPASS="${SSHPASS:-${VPS_PASSWORD:-}}"

if [ -z "${SSHPASS:-}" ]; then
  echo "Нет SSHPASS/VPS_PASSWORD для pull-deploy-env" >&2
  exit 1
fi

SSHPASS_BIN=""
if command -v sshpass >/dev/null; then
  SSHPASS_BIN="sshpass"
elif [ -x /tmp/sshpass-extract/usr/bin/sshpass ]; then
  SSHPASS_BIN="/tmp/sshpass-extract/usr/bin/sshpass"
fi

REMOTE_KEYS=(
  VK_GROUP_TOKEN VK_GROUP_ID VK_EVENTS_TOKEN
  TIMEPAD_API_TOKEN PROCULTURE_API_KEY
  POLLINATIONS_API_KEY OPENROUTER_API_KEY GEMINI_API_KEY
)

REMOTE_TEXT="$(
  SSHPASS="$SSHPASS" "$SSHPASS_BIN" -e ssh -o StrictHostKeyChecking=no "$USER@$HOST" \
    "grep -E '^($(IFS='|'; echo "${REMOTE_KEYS[*]}"))=' $REMOTE_ENV 2>/dev/null || true"
)"

python3 - "$LOCAL_ENV" "$REMOTE_TEXT" <<'PY'
import sys
from pathlib import Path

path = Path(sys.argv[1])
remote = [ln for ln in sys.argv[2].splitlines() if "=" in ln]
existing: dict[str, str] = {}
if path.is_file():
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            existing[k] = v

for line in remote:
    k, v = line.split("=", 1)
    if v.strip():
        existing[k] = v

order = [
    "SSHPASS", "VPS_HOST", "VPS_USER",
    "VK_GROUP_TOKEN", "VK_GROUP_ID", "VK_EVENTS_TOKEN",
    "TIMEPAD_API_TOKEN", "PROCULTURE_API_KEY",
    "POLLINATIONS_API_KEY", "OPENROUTER_API_KEY", "GEMINI_API_KEY",
]
out: list[str] = []
seen: set[str] = set()
for key in order:
    val = existing.get(key, "")
    if val:
        out.append(f"{key}={val}")
        seen.add(key)
for key, val in existing.items():
    if key not in seen and val:
        out.append(f"{key}={val}")
path.write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"OK: {path} ({len(out)} keys)")
PY

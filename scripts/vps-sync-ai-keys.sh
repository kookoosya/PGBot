#!/bin/bash
# На VPS: прописать AI-ключи в /opt/pgbot/.env
set -euo pipefail

ENV_FILE="${1:-/opt/pgbot/.env}"

_set_var() {
  local name="$1"
  local value="$2"
  [ -n "$value" ] || return 0
  python3 - "$ENV_FILE" "$name" "$value" <<'PY'
import re, sys
from pathlib import Path
path = Path(sys.argv[1])
name, val = sys.argv[2], sys.argv[3]
text = path.read_text(encoding="utf-8") if path.is_file() else ""
pat = r'^' + re.escape(name) + r'=.*$'
if re.search(pat, text, flags=re.M):
    text = re.sub(pat, name + '=' + val, text, flags=re.M)
else:
    if text and not text.endswith('\n'):
        text += '\n'
    text += name + '=' + val + '\n'
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(text, encoding='utf-8')
print('set', name)
PY
}

# OpenRouter из BetMasterAI на том же сервере (если есть)
if [ -z "${OPENROUTER_API_KEY:-}" ] && [ -f /root/BetMasterAI/config.json ]; then
  OPENROUTER_API_KEY="$(cd /root/BetMasterAI && python3 - <<'PY' 2>/dev/null || true
import json
import sys
from pathlib import Path
sys.path.insert(0, "/root/BetMasterAI")
from core.security_hardening import ConfigSecurity
c = json.loads(Path("/root/BetMasterAI/config.json").read_text())
key = ConfigSecurity().decrypt_secrets(c).get("api", {}).get("openrouter_api_key", "")
if key.startswith("sk-or-"):
    print(key)
PY
)"
fi

_set_var OPENROUTER_API_KEY "${OPENROUTER_API_KEY:-}"
_set_var POLLINATIONS_API_KEY "${POLLINATIONS_API_KEY:-}"
_set_var GEMINI_API_KEY "${GEMINI_API_KEY:-}"

echo "AI keys synced to $ENV_FILE"

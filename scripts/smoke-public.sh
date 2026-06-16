#!/usr/bin/env bash
# Smoke-тест публичных URL после деплоя или локально.
# Использование: bash scripts/smoke-public.sh [BASE_URL]
#
# Прод по умолчанию: https://192-210-213-135.sslip.io (см. scripts/canonical-site.sh)
#
# Переменные:
#   SMOKE_SKIP_CINEMA=1  — не проверять блок кино (для staging без данных)
#   SMOKE_MIN_CINEMA=N   — минимум фильмов (по умолчанию 1)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=canonical-site.sh
source "$SCRIPT_DIR/canonical-site.sh"

BASE="${1:-${SMOKE_BASE_URL:-$CANONICAL_SITE_URL}}"
API="${BASE%/}/api/v1"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass=0
fail=0
warn=0

check() {
  local name="$1"
  local url="$2"
  local expect="${3:-}"

  local code body
  code=$(curl -sS -o /tmp/smoke-body.txt -w "%{http_code}" --max-time 20 "$url" || echo "000")
  body=$(cat /tmp/smoke-body.txt 2>/dev/null || true)

  if [[ "$code" != "200" ]]; then
    echo -e "${RED}FAIL${NC} $name — HTTP $code ($url)"
    fail=$((fail + 1))
    return
  fi

  if [[ -n "$expect" && "$body" != *"$expect"* ]]; then
    echo -e "${RED}FAIL${NC} $name — нет «$expect» в ответе ($url)"
    fail=$((fail + 1))
    return
  fi

  echo -e "${GREEN}OK${NC}   $name"
  pass=$((pass + 1))
}

check_redirect_ok() {
  local name="$1"
  local url="$2"
  local code
  code=$(curl -sS -o /dev/null -w "%{http_code}" --max-time 20 -L "$url" || echo "000")
  if [[ "$code" == "200" ]]; then
    echo -e "${GREEN}OK${NC}   $name"
    pass=$((pass + 1))
  else
    echo -e "${RED}FAIL${NC} $name — HTTP $code ($url)"
    fail=$((fail + 1))
  fi
}

echo "Smoke: $BASE"
echo "---"

# SPA routes
check "Главная" "$BASE/" "root"
check "Афиша" "$BASE/events" "root"
check "Объявления" "$BASE/classifieds" "root"
check "Работа" "$BASE/jobs" "root"
check "Услуги" "$BASE/services" "root"
check "Карта" "$BASE/map" "root"
check "Регистрация" "$BASE/register" "root"
check "Вход в кабинет" "$BASE/cabinet/login" "root"
check "Обращения" "$BASE/complaints" "root"
check "Кабинет" "$BASE/cabinet" "root"
check "Подать обращение (deep link)" "$BASE/complaints?new=1" "root"
check "ИИ-помощник" "$BASE/ai" "root"
check "VK Mini App" "$BASE/vk" "root"
check "Подать объявление (deep link)" "$BASE/classifieds?new=1" "root"
check "Обращение (deep link)" "$BASE/complaints?issue=1" "root"

# API
check "Health" "${BASE%/}/health" "ok"
check "API today" "$API/public/today" "upcoming_events"
check "API public info" "$API/public/info" "site_url"

# На проде API должен отдавать тот же канонический URL
if [[ "$BASE" == *"$CANONICAL_SITE_HOST"* ]]; then
  site_url=$(curl -sS --max-time 20 "$API/public/info" | python3 -c "import sys,json; print(json.load(sys.stdin).get('site_url',''))")
  if [[ "$site_url" != "$CANONICAL_SITE_URL" ]]; then
    echo -e "${RED}FAIL${NC} API site_url=$site_url (ожидался $CANONICAL_SITE_URL)"
    fail=$((fail + 1))
  else
    echo -e "${GREEN}OK${NC}   API site_url canonical"
    pass=$((pass + 1))
  fi
  portal_complaints=$(curl -sS --max-time 20 "$API/public/info" | python3 -c "import sys,json; print(json.load(sys.stdin).get('portal_links',{}).get('complaints',''))")
  if [[ "$portal_complaints" != "$CANONICAL_SITE_URL/complaints" ]]; then
    echo -e "${RED}FAIL${NC} portal_links.complaints=$portal_complaints"
    fail=$((fail + 1))
  else
    echo -e "${GREEN}OK${NC}   portal_links use sslip.io"
    pass=$((pass + 1))
  fi
fi
check "API events" "$API/public/events" "items"
check "API classifieds" "$API/classifieds" "items"
check "API classifieds categories" "$API/classifieds/categories" "value"

# Critical API flows (validation + schema)
if python3 "$SCRIPT_DIR/smoke_scenarios.py" "$API"; then
  pass=$((pass + 1))
else
  fail=$((fail + 1))
fi

# Cinema block — real films, not culture events
if [[ "${SMOKE_SKIP_CINEMA:-}" == "1" ]]; then
  echo -e "${YELLOW}SKIP${NC} cinema block (SMOKE_SKIP_CINEMA=1)"
  warn=$((warn + 1))
else
  MIN_CINEMA="${SMOKE_MIN_CINEMA:-1}"
  if python3 "$SCRIPT_DIR/smoke_check_cinema.py" "$API/public/today" --min "$MIN_CINEMA"; then
    pass=$((pass + 1))
  else
    fail=$((fail + 1))
  fi
fi

# Literary CSS deployed (bundle hash changes each build — check design token)
if curl -sS --max-time 20 "$BASE/" | grep -qE 'literary|index-.*\.css'; then
  echo -e "${GREEN}OK${NC}   Literary assets"
  pass=$((pass + 1))
else
  echo -e "${RED}FAIL${NC} Literary assets — CSS bundle not found"
  fail=$((fail + 1))
fi

echo "---"
echo "Итого: $pass OK, $fail FAIL${warn:+, $warn SKIP}"

if [[ "$fail" -gt 0 ]]; then
  exit 1
fi

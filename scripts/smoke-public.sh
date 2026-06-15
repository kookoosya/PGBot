#!/usr/bin/env bash
# Smoke-тест публичных URL после деплоя или локально.
# Использование: bash scripts/smoke-public.sh [BASE_URL]
#
# Переменные:
#   SMOKE_SKIP_CINEMA=1  — не проверять блок кино (для staging без данных)
#   SMOKE_MIN_CINEMA=N   — минимум фильмов (по умолчанию 1)
set -euo pipefail

BASE="${1:-${SMOKE_BASE_URL:-http://localhost:5173}}"
API="${BASE%/}/api/v1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
check "ИИ-помощник" "$BASE/ai" "root"

# API
check "API today" "$API/public/today" "upcoming_events"

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

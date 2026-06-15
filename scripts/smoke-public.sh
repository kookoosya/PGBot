#!/usr/bin/env bash
# Smoke-тест публичных URL после деплоя или локально.
# Использование: bash scripts/smoke-public.sh [BASE_URL]
set -euo pipefail

BASE="${1:-http://localhost:5173}"
API="${BASE%/}/api/v1"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

pass=0
fail=0

check() {
  local name="$1"
  local url="$2"
  local expect="${3:-}"

  local code body
  code=$(curl -sS -o /tmp/smoke-body.txt -w "%{http_code}" --max-time 15 "$url" || echo "000")
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

echo "Smoke: $BASE"
echo "---"

# SPA routes — ожидаем index.html с корневым div
check "Главная" "$BASE/" "root"
check "Афиша" "$BASE/events" "root"
check "Объявления" "$BASE/classifieds" "root"
check "Работа" "$BASE/jobs" "root"
check "Услуги" "$BASE/services" "root"
check "Карта" "$BASE/map" "root"
check "Регистрация" "$BASE/register" "root"
check "ИИ-помощник" "$BASE/ai" "root"

# API
check "API today" "$API/public/today" "upcoming_events"

echo "---"
echo "Итого: $pass OK, $fail FAIL"

if [[ "$fail" -gt 0 ]]; then
  exit 1
fi

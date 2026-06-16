#!/usr/bin/env bash
# Диагностика источников афиши (локально или на VPS).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ -f docker-compose.prod.yml ] && docker compose -f docker-compose.prod.yml ps backend >/dev/null 2>&1; then
  docker compose -f docker-compose.prod.yml exec -T backend python scripts/check_event_sources.py
else
  cd backend && python3 scripts/check_event_sources.py
fi

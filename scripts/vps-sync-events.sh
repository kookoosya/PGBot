#!/usr/bin/env bash
# Запуск синхронизации афиши на VPS (из cron или вручную).
# Использование: bash scripts/vps-sync-events.sh [cinema|all|enrich]
set -euo pipefail

MODE="${1:-cinema}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

COMPOSE="docker compose -f docker-compose.prod.yml"
LOG_TAG="[pgbot-sync]"

echo "$LOG_TAG $(date -Is) mode=$MODE"

$COMPOSE exec -T backend python scripts/sync_all_events.py --mode "$MODE"
EXIT=$?

echo "$LOG_TAG $(date -Is) finished exit=$EXIT"
exit "$EXIT"

#!/bin/bash
# Выполняется НА VPS в /opt/pgbot после git pull.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=canonical-site.sh
source "$SCRIPT_DIR/canonical-site.sh"

cd /opt/pgbot

bash scripts/vps-sync-ai-keys.sh 2>/dev/null || true
bash scripts/setup-russia-mirror.sh
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head \
  || docker compose -f docker-compose.prod.yml exec -T backend alembic stamp head
docker compose -f docker-compose.prod.yml exec -T backend python scripts/seed_events.py 2>/dev/null || true
bash scripts/install-vps-cron.sh /opt/pgbot
bash scripts/vps-sync-events.sh cinema 2>/dev/null || true
bash scripts/smoke-public.sh "$CANONICAL_SITE_URL"

echo "Deploy OK: $CANONICAL_SITE_URL"

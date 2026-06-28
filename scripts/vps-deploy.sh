#!/bin/bash
# Выполняется НА VPS в /opt/pgbot после git pull.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=canonical-site.sh
source "$SCRIPT_DIR/canonical-site.sh"

cd /opt/pgbot

export GIT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

bash scripts/vps-sync-ai-keys.sh 2>/dev/null || true
if [ -f /opt/pgbot/.env ]; then
  set -a
  # shellcheck disable=SC1091
  source /opt/pgbot/.env
  set +a
fi
bash scripts/cloudflare-dns-only.sh 2>/dev/null || true
docker compose -f docker-compose.prod.yml up -d --build
bash scripts/setup-cloudflare-origin.sh 2>/dev/null || true
bash scripts/setup-primary-domain.sh
docker compose -f docker-compose.prod.yml restart nginx backend
bash scripts/wait-for-health.sh http://127.0.0.1:8088/health
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head \
  || docker compose -f docker-compose.prod.yml exec -T backend alembic stamp head
docker compose -f docker-compose.prod.yml exec -T backend python scripts/seed_events.py 2>/dev/null || true
docker compose -f docker-compose.prod.yml exec -T backend python scripts/sync_map_once.py 2>/dev/null || true
bash scripts/install-vps-cron.sh /opt/pgbot
bash scripts/vps-sync-events.sh cinema 2>/dev/null || true
bash scripts/setup-ru-direct-dns-check.sh || true
SMOKE_LOCAL_API=1 bash scripts/smoke-public.sh "$CANONICAL_SITE_URL"

echo "Deploy OK: $CANONICAL_SITE_URL"

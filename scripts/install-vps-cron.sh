#!/usr/bin/env bash
# Установка cron-задач синхронизации афиши на VPS.
set -euo pipefail

ROOT="${1:-/opt/pgbot}"
LOG_FILE="/var/log/pgbot-sync.log"
CRON_FILE="/etc/cron.d/pgbot-events"

touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

cat > "$CRON_FILE" <<EOF
# PGBot — автосинхронизация афиши (idempotent upsert)
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

# Кино: Kinopskov, Mirage, Silver, Orbilet — каждые 8 часов
0 */8 * * * root cd ${ROOT} && bash scripts/vps-sync-events.sh cinema >> ${LOG_FILE} 2>&1

# Полная синхронизация всех источников — раз в сутки в 03:15
15 3 * * * root cd ${ROOT} && bash scripts/vps-sync-events.sh all >> ${LOG_FILE} 2>&1

# Карта: справочник + OSM + очистка дублей — каждые 6 часов
30 */6 * * * root cd ${ROOT} && docker compose -f docker-compose.prod.yml exec -T backend python scripts/sync_map_once.py >> ${LOG_FILE} 2>&1
EOF

chmod 644 "$CRON_FILE"
echo "Cron installed: $CRON_FILE"
cat "$CRON_FILE"

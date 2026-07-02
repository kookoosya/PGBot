#!/bin/bash
# Export places and taxi for stage-02 backup (no reviews/complaints).
set -euo pipefail
cd /opt/pgbot
OUT_DIR="/opt/pgbot/docs/factual-integrity/backups"
mkdir -p "$OUT_DIR"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d narodny_kontrol -c \
  "\copy (SELECT id,name,category,address,latitude,longitude,phone,opening_hours,website,osm_id,yandex_id,yandex_url,external_source,is_active,last_synced_at FROM places ORDER BY id) TO STDOUT WITH CSV HEADER" \
  > "$OUT_DIR/places-before-${TS}.csv"
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d narodny_kontrol -c \
  "\copy (SELECT id,name,phone,phones_extra,description,is_24h,rating,price_from,sort_order,is_active FROM taxi_services ORDER BY id) TO STDOUT WITH CSV HEADER" \
  > "$OUT_DIR/taxi-before-${TS}.csv"
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d narodny_kontrol -t -A -c \
  "SELECT 'places_active='||count(*) FILTER (WHERE is_active) FROM places;"
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d narodny_kontrol -t -A -c \
  "SELECT 'places_inactive='||count(*) FILTER (WHERE NOT is_active) FROM places;"
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d narodny_kontrol -t -A -c \
  "SELECT category||':'||count(*) FROM places WHERE is_active GROUP BY category ORDER BY category;"
echo "BACKUP_DIR=$OUT_DIR"
echo "BACKUP_TS=$TS"

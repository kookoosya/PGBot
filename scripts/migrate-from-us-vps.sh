#!/bin/bash
# Перенос PGBot с US VPS на новый RU VPS (Selectel / Timeweb / Yandex Cloud)
# Запуск на НОВОМ сервере: OLD_VPS=root@192.210.213.135 bash scripts/migrate-from-us-vps.sh
set -euo pipefail

OLD_VPS="${OLD_VPS:-root@192.210.213.135}"
APP_DIR="${APP_DIR:-/opt/pgbot}"
RU_DOMAIN="${RU_DOMAIN:-pushkinskie-gory.ru}"
REPO="${REPO:-https://github.com/kookoosya/PGBot.git}"

echo "==> Бэкап PostgreSQL с ${OLD_VPS}..."
mkdir -p /tmp/pgbot-migrate
ssh -o StrictHostKeyChecking=accept-new "$OLD_VPS" \
  "cd ${APP_DIR} && docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U postgres narodny_kontrol" \
  > /tmp/pgbot-migrate/db.sql

echo "==> Копия .env..."
ssh "$OLD_VPS" "cat ${APP_DIR}/.env" > /tmp/pgbot-migrate/.env

echo "==> Bootstrap на этом сервере..."
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

mkdir -p "$(dirname "$APP_DIR")"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"
git pull origin main

cp /tmp/pgbot-migrate/.env "$APP_DIR/.env"
sed -i "s|^PUBLIC_SITE_URL=.*|PUBLIC_SITE_URL=https://${RU_DOMAIN}|" "$APP_DIR/.env"
sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=https://${RU_DOMAIN},https://www.${RU_DOMAIN},https://pushkinskie-gory.xyz,https://www.pushkinskie-gory.xyz|" "$APP_DIR/.env"

docker compose -f docker-compose.prod.yml up -d --build
sleep 15
docker compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d narodny_kontrol < /tmp/pgbot-migrate/db.sql || true

PRIMARY_DOMAIN="$RU_DOMAIN" bash scripts/setup-dual-domain.sh
docker compose -f docker-compose.prod.yml restart backend nginx

echo "DONE: https://${RU_DOMAIN}/health"
echo "Обновите A-запись ${RU_DOMAIN} на IP этого сервера: $(curl -s ifconfig.me || hostname -I | awk '{print $1}')"

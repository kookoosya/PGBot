#!/bin/bash
# Deploy PGBot to VPS without conflicting with other projects
# Runs on port 8088 (nginx) — configure main nginx to proxy your domain here

set -e
DEPLOY_DIR="/opt/pgbot"
REPO_URL="${REPO_URL:-https://github.com/kookoosya/PGBot.git}"
BRANCH="${BRANCH:-cursor/narodny-kontrol-mvp-e7fb}"

echo "=== PGBot Deploy ==="

if [ ! -d "$DEPLOY_DIR" ]; then
  git clone -b "$BRANCH" "$REPO_URL" "$DEPLOY_DIR"
fi

cd "$DEPLOY_DIR"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "!!! Отредактируйте $DEPLOY_DIR/.env перед запуском !!!"
  exit 1
fi

docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "=== Готово ==="
echo "Локальный URL: http://127.0.0.1:8088"
echo ""
echo "Добавьте в основной nginx (не трогая другие проекты):"
echo ""
cat << 'NGINX'
server {
    listen 80;
    server_name YOUR_DOMAIN.ru;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

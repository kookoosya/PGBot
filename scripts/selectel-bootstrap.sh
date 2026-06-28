#!/bin/bash
# Первичный деплой PGBot на чистый RU VPS (Selectel / Timeweb / Yandex Cloud)
set -euo pipefail

REPO="${REPO:-https://github.com/kookoosya/PGBot.git}"
APP_DIR="${APP_DIR:-/opt/pgbot}"
RU_DOMAIN="${RU_DOMAIN:-pushkinskie-gory.ru}"

echo "==> Установка Docker..."
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable --now docker
fi

echo "==> Клонирование репозитория..."
mkdir -p "$(dirname "$APP_DIR")"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"
git pull origin main

echo "==> .env (скопируйте секреты с US VPS вручную при первом запуске)"
if [ ! -f .env ]; then
  cp .env.example .env 2>/dev/null || touch .env
fi

echo "==> Docker Compose prod..."
docker compose -f docker-compose.prod.yml up -d --build

echo "==> Nginx + SSL для ${RU_DOMAIN}..."
PRIMARY_DOMAIN="${RU_DOMAIN}" bash scripts/setup-dual-domain.sh

echo "DONE: https://${RU_DOMAIN}/health"

#!/bin/bash
# HTTPS для .ru + .xyz на одном VPS (пока DNS указывает сюда)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=canonical-site.sh
source "${SCRIPT_DIR}/canonical-site.sh"

RU_DOMAIN="${RU_DOMAIN:-pushkinskie-gory.ru}"
XYZ_DOMAIN="${XYZ_DOMAIN:-pushkinskie-gory.xyz}"
PRIMARY_DOMAIN="${PRIMARY_DOMAIN:-${RU_DOMAIN}}"
UPSTREAM="${UPSTREAM:-http://127.0.0.1:8088}"
CONF="/etc/nginx/sites-available/pgbot-primary"

ALL_NAMES="${RU_DOMAIN} www.${RU_DOMAIN} ${XYZ_DOMAIN} www.${XYZ_DOMAIN}"

cat > "$CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${ALL_NAMES};

    client_max_body_size 10m;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass ${UPSTREAM};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
EOF

mkdir -p /var/www/certbot
ln -sf "$CONF" /etc/nginx/sites-enabled/pgbot-primary
rm -f /etc/nginx/sites-enabled/pushkiny-mirror /etc/nginx/sites-enabled/pgbot-sslip 2>/dev/null || true

for f in /etc/nginx/sites-enabled/*; do
  sed -i 's/ listen 80 default_server;/ listen 80;/' "$f" 2>/dev/null || true
  sed -i 's/ listen \[::\]:80 default_server;/ listen [::]:80;/' "$f" 2>/dev/null || true
done

nginx -t
systemctl reload nginx

if command -v certbot >/dev/null; then
  certbot --nginx \
    -d "${RU_DOMAIN}" -d "www.${RU_DOMAIN}" \
    -d "${XYZ_DOMAIN}" -d "www.${XYZ_DOMAIN}" \
    --non-interactive --agree-tos --register-unsafely-without-email --redirect \
    || echo "CERTBOT_PENDING: проверьте DNS A-записи для .ru и .xyz"
fi

ENV="/opt/pgbot/.env"
SITE_URL="https://${PRIMARY_DOMAIN}"
CORS="${SITE_URL},https://www.${PRIMARY_DOMAIN},https://${XYZ_DOMAIN},https://www.${XYZ_DOMAIN}"

if [ -f "$ENV" ]; then
  if grep -q '^PUBLIC_SITE_URL=' "$ENV"; then
    sed -i "s|^PUBLIC_SITE_URL=.*|PUBLIC_SITE_URL=${SITE_URL}|" "$ENV"
  else
    echo "PUBLIC_SITE_URL=${SITE_URL}" >> "$ENV"
  fi
  if grep -q '^CORS_ORIGINS=' "$ENV"; then
    sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=${CORS}|" "$ENV"
  else
    echo "CORS_ORIGINS=${CORS}" >> "$ENV"
  fi
fi

if [ -d /opt/pgbot ]; then
  cd /opt/pgbot
  docker compose -f docker-compose.prod.yml restart backend nginx 2>/dev/null || \
  docker compose -f docker-compose.prod.yml up -d
fi

echo "PRIMARY=${SITE_URL}"
echo "CORS=${CORS}"
curl -sk "https://${PRIMARY_DOMAIN}/health" 2>/dev/null | head -c 200 || true
echo

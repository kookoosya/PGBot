#!/bin/bash
# Переключить PGBot на pushkinskie-gory.xyz
set -euo pipefail

DOMAIN="pushkinskie-gory.xyz"
VPS_IP="192.210.213.135"
UPSTREAM="http://127.0.0.1:8088"
CONF="/etc/nginx/sites-available/pgbot-primary"

cat > "$CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

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

# Снять default с betmasterai если перехватывает
for f in /etc/nginx/sites-enabled/*; do
  sed -i 's/ listen 80 default_server;/ listen 80;/' "$f" 2>/dev/null || true
  sed -i 's/ listen \[::\]:80 default_server;/ listen [::]:80;/' "$f" 2>/dev/null || true
done

nginx -t
systemctl reload nginx

# SSL (если DNS уже на VPS)
if command -v certbot >/dev/null; then
  certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" \
    --non-interactive --agree-tos --register-unsafely-without-email --redirect \
    || echo "CERTBOT_PENDING: DNS may not point to VPS yet"
fi

ENV="/opt/pgbot/.env"
SITE_URL="https://${DOMAIN}"
if [ -f "$ENV" ]; then
  if grep -q '^PUBLIC_SITE_URL=' "$ENV"; then
    sed -i "s|^PUBLIC_SITE_URL=.*|PUBLIC_SITE_URL=${SITE_URL}|" "$ENV"
  else
    echo "PUBLIC_SITE_URL=${SITE_URL}" >> "$ENV"
  fi
  if grep -q '^CORS_ORIGINS=' "$ENV"; then
    sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=${SITE_URL},https://www.${DOMAIN}|" "$ENV"
  else
    echo "CORS_ORIGINS=${SITE_URL},https://www.${DOMAIN}" >> "$ENV"
  fi
fi

if [ -d /opt/pgbot ]; then
  cd /opt/pgbot
  docker compose -f docker-compose.prod.yml restart backend nginx 2>/dev/null || \
  docker compose -f docker-compose.prod.yml up -d
fi

echo "--- DNS check ---"
dig +short "${DOMAIN}" A || true
echo "--- HTTP local ---"
curl -sI "http://127.0.0.1/" -H "Host: ${DOMAIN}" | head -5 || true
echo "--- Health ---"
curl -sk "https://${DOMAIN}/health" 2>/dev/null | head -c 300 || \
curl -s "http://${DOMAIN}/health" 2>/dev/null | head -c 300 || true
echo
echo "SITE_URL=${SITE_URL}"

#!/bin/bash
# Открыть PGBot по короткому адресу http://192.210.213.135/ (без sslip, без :8088)
# Запуск на VPS: bash fix-ip-access.sh
set -euo pipefail

VPS_IP="192.210.213.135"
UPSTREAM="http://127.0.0.1:8088"
CONF="/etc/nginx/sites-available/pushkiny-mirror"
SSLIP="192-210-213-135.sslip.io"
CERT_DIR=""

if [ -d "/etc/letsencrypt/live/${SSLIP}" ]; then
  CERT_DIR="/etc/letsencrypt/live/${SSLIP}"
elif [ -f "/etc/letsencrypt/live/${SSLIP}/fullchain.pem" ]; then
  CERT_DIR="/etc/letsencrypt/live/${SSLIP}"
else
  # fallback: first cert dir
  CERT_DIR="$(ls -d /etc/letsencrypt/live/*/fullchain.pem 2>/dev/null | head -1 | xargs dirname 2>/dev/null || true)"
fi

cp "$CONF" "${CONF}.bak.$(date +%s)" 2>/dev/null || true

# HTTP: IP → PGBot напрямую; sslip.io → редирект на HTTPS (если cert есть)
cat > "$CONF" <<EOF
# PGBot — короткий URL по IP (РФ, без sslip в адресной строке)
server {
    listen 80;
    listen [::]:80;
    server_name ${VPS_IP};

    client_max_body_size 10m;

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

server {
    listen 80;
    listen [::]:80;
    server_name ${SSLIP};

    return 301 https://\$host\$request_uri;
}
EOF

if [ -n "$CERT_DIR" ] && [ -f "${CERT_DIR}/fullchain.pem" ]; then
  cat >> "$CONF" <<EOF

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${VPS_IP} ${SSLIP};

    ssl_certificate ${CERT_DIR}/fullchain.pem;
    ssl_certificate_key ${CERT_DIR}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 10m;

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
fi

ln -sf "$CONF" /etc/nginx/sites-enabled/pushkiny-mirror

# Убрать default betmasterai с перехватом IP (если мешает)
if grep -q "default_server" /etc/nginx/sites-enabled/betmasterai 2>/dev/null; then
  sed -i 's/ listen 80 default_server;/ listen 80;/' /etc/nginx/sites-enabled/betmasterai 2>/dev/null || true
  sed -i 's/ listen \[::\]:80 default_server;/ listen [::]:80;/' /etc/nginx/sites-enabled/betmasterai 2>/dev/null || true
fi

nginx -t
systemctl reload nginx

ENV="/opt/pgbot/.env"
if [ -f "$ENV" ]; then
  if grep -q '^PUBLIC_SITE_URL=' "$ENV"; then
    sed -i "s|^PUBLIC_SITE_URL=.*|PUBLIC_SITE_URL=http://${VPS_IP}|" "$ENV"
  else
    echo "PUBLIC_SITE_URL=http://${VPS_IP}" >> "$ENV"
  fi
  if grep -q '^CORS_ORIGINS=' "$ENV"; then
    sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=http://${VPS_IP},http://${VPS_IP}:8088,https://${SSLIP}|" "$ENV"
  fi
  cd /opt/pgbot && docker compose -f docker-compose.prod.yml restart backend 2>/dev/null || true
fi

# fail2ban: разблокировать частые IP (опционально)
if command -v fail2ban-client >/dev/null; then
  fail2ban-client status sshd 2>/dev/null | head -5 || true
fi

echo ""
echo "=== Готово ==="
echo "Сайт (короткий):  http://${VPS_IP}/"
echo "Запасной:         http://${VPS_IP}:8088/"
if [ -n "$CERT_DIR" ]; then
  echo "HTTPS sslip:      https://${SSLIP}/"
fi
echo ""
curl -sI "http://127.0.0.1/" -H "Host: ${VPS_IP}" | head -3

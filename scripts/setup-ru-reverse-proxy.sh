#!/bin/bash
# Reverse-proxy на VPS в России → origin в США (192.210.213.135).
# Запускать НА РОССИЙСКОМ VPS (Ubuntu/Debian), не на US origin.
#
# После установки: в Cloudflare DNS (серое облако) A @ и www → IP ЭТОГО RU-VPS.
set -euo pipefail

DOMAIN="${DOMAIN:-pushkinskie-gory.xyz}"
ORIGIN_IP="${ORIGIN_IP:-192.210.213.135}"
ORIGIN_HOST="${ORIGIN_HOST:-pushkinskie-gory.xyz}"
CONF="/etc/nginx/sites-available/pgbot-ru-proxy"

if ! command -v nginx >/dev/null; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y nginx certbot python3-certbot-nginx
fi

mkdir -p /var/www/certbot

cat > "$CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name ${DOMAIN} www.${DOMAIN};

    client_max_body_size 10m;

    # certbot заполнит ssl_certificate после первого запуска
    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    location / {
        proxy_pass https://${ORIGIN_IP};
        proxy_ssl_server_name on;
        proxy_ssl_name ${ORIGIN_HOST};
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Host ${ORIGIN_HOST};
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 30s;
    }
}
EOF

ln -sf "$CONF" /etc/nginx/sites-enabled/pgbot-ru-proxy
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true

# Временный HTTP-only конфиг для certbot, если сертификата ещё нет
if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  cat > "$CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass https://${ORIGIN_IP};
        proxy_ssl_server_name on;
        proxy_ssl_name ${ORIGIN_HOST};
        proxy_ssl_verify off;
        proxy_set_header Host ${ORIGIN_HOST};
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
  nginx -t && systemctl reload nginx
  certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" \
    --non-interactive --agree-tos --register-unsafely-without-email --redirect
  # Перезаписать полный конфиг с SSL upstream
  bash "$0"
  exit 0
fi

nginx -t
systemctl enable nginx
systemctl reload nginx

echo ""
echo "=== RU proxy готов ==="
echo "Домен: https://${DOMAIN}"
echo "Origin: https://${ORIGIN_IP} (Host: ${ORIGIN_HOST})"
echo ""
echo "Cloudflare → DNS → A @ и www → $(curl -sS --max-time 5 ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')"
echo "Облако: DNS only (серое)"
echo ""
curl -sS --max-time 10 -o /dev/null -w "Local health via proxy: HTTP %{http_code}\n" "http://127.0.0.1/health" -H "Host: ${DOMAIN}" || true

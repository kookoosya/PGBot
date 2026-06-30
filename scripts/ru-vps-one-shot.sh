#!/bin/bash
# Запуск на RU VPS (FirstByte): root@185.103.105.79
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update -qq
apt-get install -y -qq nginx curl ca-certificates certbot python3-certbot-nginx openssh-server
systemctl enable --now ssh nginx

DOMAIN=pushkinskie-gory.xyz
ORIGIN=192.210.213.135

mkdir -p /var/www/certbot
cat > /etc/nginx/sites-available/pgbot-ru-proxy <<NGX
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};
    client_max_body_size 10m;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass https://${ORIGIN};
        proxy_ssl_server_name on;
        proxy_ssl_name ${DOMAIN};
        proxy_ssl_verify off;
        proxy_http_version 1.1;
        proxy_set_header Host ${DOMAIN};
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 30s;
    }
}
NGX

ln -sf /etc/nginx/sites-available/pgbot-ru-proxy /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "HTTP proxy OK"
curl -sS -o /dev/null -w "local:%{http_code}\n" http://127.0.0.1/health -H "Host: ${DOMAIN}" || true

# SSL — только когда DNS @ → 185.103.105.79
if dig +short ${DOMAIN} A | grep -q '185.103.105.79'; then
  certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" \
    --non-interactive --agree-tos --register-unsafely-without-email --redirect
  echo "HTTPS OK"
else
  echo "DNS ещё не на RU IP. Porkbun: A @ и www → 185.103.105.79"
  echo "Потом: certbot --nginx -d ${DOMAIN} -d www.${DOMAIN} --agree-tos -m admin@${DOMAIN} --redirect"
fi

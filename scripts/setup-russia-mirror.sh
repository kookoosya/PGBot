#!/bin/bash
# Зеркало без VPN: sslip.io + прямой IP на порту 80
set -euo pipefail

MIRROR="192-210-213-135.sslip.io"
SITE_CONF="/etc/nginx/sites-available/pushkiny-mirror"

cat > "$SITE_CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $MIRROR 192.210.213.135;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
EOF

ln -sf "$SITE_CONF" /etc/nginx/sites-enabled/pushkiny-mirror

# default_server на IP тоже ведёт на портал (не на 8080)
if [ -f /etc/nginx/sites-enabled/default ]; then
  sed -i 's|proxy_pass http://127.0.0.1:8080|proxy_pass http://127.0.0.1:8088|g' /etc/nginx/sites-enabled/default 2>/dev/null || true
fi

nginx -t
systemctl reload nginx

if command -v certbot >/dev/null; then
  certbot --nginx -d "$MIRROR" --non-interactive --agree-tos --register-unsafely-without-email --redirect || true
fi

ENV_FILE="/opt/pgbot/.env"
if [ -f "$ENV_FILE" ]; then
  if grep -q '^PUBLIC_SITE_URL=' "$ENV_FILE"; then
    sed -i "s|^PUBLIC_SITE_URL=.*|PUBLIC_SITE_URL=https://$MIRROR|" "$ENV_FILE"
  else
    echo "PUBLIC_SITE_URL=https://$MIRROR" >> "$ENV_FILE"
  fi
fi

echo "Mirror: https://$MIRROR"
echo "HTTP IP: http://192.210.213.135:8088"

#!/bin/bash
# Nginx + HTTPS только для sslip.io (единственный рабочий прод сейчас).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=canonical-site.sh
source "$SCRIPT_DIR/canonical-site.sh"

VPS_IP="192.210.213.135"
UPSTREAM="http://127.0.0.1:8088"

proxy_block() {
  cat <<EOF
    client_max_body_size 10m;

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    location / {
        proxy_pass $UPSTREAM;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
EOF
}

SITE_CONF="/etc/nginx/sites-available/pushkiny-mirror"
cat > "$SITE_CONF" <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name $CANONICAL_SITE_HOST $VPS_IP;

$(proxy_block)
}
EOF
ln -sf "$SITE_CONF" /etc/nginx/sites-enabled/pushkiny-mirror
rm -f /etc/nginx/sites-enabled/pgbot-sslip 2>/dev/null || true

# Убираем старые конфиги с .ru — сейчас не используем
rm -f /etc/nginx/sites-enabled/pushkiny-primary 2>/dev/null || true

if [ -f /etc/nginx/sites-enabled/default ]; then
  sed -i "s|proxy_pass http://127.0.0.1:8080|proxy_pass $UPSTREAM|g" /etc/nginx/sites-enabled/default 2>/dev/null || true
fi

nginx -t
systemctl reload nginx

if command -v certbot >/dev/null; then
  certbot --nginx -d "$CANONICAL_SITE_HOST" \
    --non-interactive --agree-tos --register-unsafely-without-email --redirect 2>/dev/null || true
fi

ENV_FILE="/opt/pgbot/.env"
if [ -f "$ENV_FILE" ]; then
  if grep -q '^PUBLIC_SITE_URL=' "$ENV_FILE"; then
    sed -i "s|^PUBLIC_SITE_URL=.*|PUBLIC_SITE_URL=$CANONICAL_SITE_URL|" "$ENV_FILE"
  else
    echo "PUBLIC_SITE_URL=$CANONICAL_SITE_URL" >> "$ENV_FILE"
  fi
fi

echo "Канонический URL: $CANONICAL_SITE_URL"

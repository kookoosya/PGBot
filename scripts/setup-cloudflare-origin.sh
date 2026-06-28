#!/bin/bash
# Nginx на origin: real IP клиентов через Cloudflare + доверенные CF-диапазоны
set -euo pipefail

CF_CONF="/etc/nginx/conf.d/cloudflare-real-ip.conf"
CF_IPS="/tmp/cloudflare-ips.txt"

curl -fsSL https://www.cloudflare.com/ips-v4 -o "${CF_IPS}.v4" || true
curl -fsSL https://www.cloudflare.com/ips-v6 -o "${CF_IPS}.v6" || true

cat > "$CF_CONF" <<'HEADER'
# Cloudflare — real client IP (auto-generated)
real_ip_header CF-Connecting-IP;
real_ip_recursive on;
HEADER

for ip in $(cat "${CF_IPS}.v4" 2>/dev/null); do
  echo "set_real_ip_from ${ip};" >> "$CF_CONF"
done
for ip in $(cat "${CF_IPS}.v6" 2>/dev/null); do
  echo "set_real_ip_from ${ip};" >> "$CF_CONF"
done

# Fallback если curl не сработал
if ! grep -q set_real_ip_from "$CF_CONF" 2>/dev/null; then
  cat >> "$CF_CONF" <<'FALLBACK'
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
set_real_ip_from 141.101.64.0/18;
set_real_ip_from 108.162.192.0/18;
set_real_ip_from 190.93.240.0/20;
set_real_ip_from 188.114.96.0/20;
set_real_ip_from 197.234.240.0/22;
set_real_ip_from 198.41.128.0/17;
set_real_ip_from 162.158.0.0/15;
set_real_ip_from 104.16.0.0/13;
set_real_ip_from 104.24.0.0/14;
set_real_ip_from 172.64.0.0/13;
set_real_ip_from 131.0.72.0/22;
FALLBACK
fi

mkdir -p /etc/nginx/conf.d
nginx -t
systemctl reload nginx

echo "Cloudflare real_ip configured: $CF_CONF"

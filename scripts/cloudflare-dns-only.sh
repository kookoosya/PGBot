#!/bin/bash
# Переключить A @ и www на DNS only (серое облако) — обязательно для доступа из РФ.
set -euo pipefail

DOMAIN="${DOMAIN:-pushkinskie-gory.xyz}"
ORIGIN_IP="${ORIGIN_IP:-192.210.213.135}"
CF_API_TOKEN="${CF_API_TOKEN:-${CLOUDFLARE_API_TOKEN:-}}"

if [[ -z "$CF_API_TOKEN" ]]; then
  echo "SKIP: нет CF_API_TOKEN — переключи вручную: Cloudflare → DNS → серое облако для @ и www"
  exit 0
fi

ZONE_ID="${CF_ZONE_ID:-}"
if [[ -z "$ZONE_ID" ]]; then
  ZONE_ID=$(curl -fsS -H "Authorization: Bearer ${CF_API_TOKEN}" \
    "https://api.cloudflare.com/client/v4/zones?name=${DOMAIN}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result'][0]['id'] if d.get('result') else '')")
fi

if [[ -z "$ZONE_ID" ]]; then
  echo "FAIL: zone not found for ${DOMAIN}"
  exit 1
fi

echo "Zone: ${ZONE_ID}"

patch_record() {
  local name="$1"
  local rec_id
  rec_id=$(curl -fsS -H "Authorization: Bearer ${CF_API_TOKEN}" \
    "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=A&name=${name}" \
    | python3 -c "import sys,json; r=json.load(sys.stdin)['result']; print(r[0]['id'] if r else '')")
  if [[ -z "$rec_id" ]]; then
    echo "WARN: no A record for ${name}"
    return 0
  fi
  curl -fsS -X PATCH "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${rec_id}" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "{\"type\":\"A\",\"name\":\"${name}\",\"content\":\"${ORIGIN_IP}\",\"proxied\":false,\"ttl\":300}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('success') else d)"
  echo " → DNS only: ${name}"
}

patch_record "${DOMAIN}"
patch_record "www.${DOMAIN}"

echo "=== verify ==="
bash "$(dirname "$0")/setup-ru-direct-dns-check.sh"

#!/bin/bash
# Проверка: домен смотрит на origin напрямую (доступ из РФ), а не на Cloudflare Proxied.
set -euo pipefail

DOMAIN="${DOMAIN:-pushkinskie-gory.xyz}"
ORIGIN_IP="${ORIGIN_IP:-192.210.213.135}"

echo "=== DNS A для ${DOMAIN} ==="
RESOLVED=$(dig +short "$DOMAIN" A | head -1)
echo "A record: ${RESOLVED:-<empty>}"

if [[ -z "$RESOLVED" ]]; then
  echo "FAIL: нет A-записи"
  exit 1
fi

if [[ "$RESOLVED" == "$ORIGIN_IP" ]]; then
  echo "OK: DNS указывает на origin ${ORIGIN_IP} (DNS only — правильно для РФ)"
elif [[ "$RESOLVED" == 104.* ]] || [[ "$RESOLVED" == 172.67.* ]]; then
  echo "FAIL: DNS указывает на Cloudflare Proxied (${RESOLVED})"
  echo "      В Cloudflare → DNS → Records → кликни облако → DNS only (серое)"
  echo "      См. docs/RU_ACCESS_FIX.md"
  exit 2
else
  echo "WARN: A=${RESOLVED}, ожидали ${ORIGIN_IP}"
fi

echo "=== HTTPS health ==="
curl -fsS --max-time 15 "https://${DOMAIN}/health" | head -c 200
echo
echo "OK"

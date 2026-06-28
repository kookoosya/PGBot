#!/bin/bash
# Инструкция: DNS pushkinskie-gory.ru → VPS PGBot
set -euo pipefail

VPS_IP="${VPS_IP:-192.210.213.135}"
RU_DOMAIN="${RU_DOMAIN:-pushkinskie-gory.ru}"

echo "=============================================="
echo " DNS для доступа из России"
echo "=============================================="
echo
echo "Сейчас ${RU_DOMAIN} указывает НЕ на PGBot (часто Tilda/parking)."
echo "Нужно в панели reg.ru / nic.ru / Timeweb:"
echo
echo "  1. Удалить parking / перенаправление / конструктор Tilda"
echo "  2. Добавить записи:"
echo
echo "     Тип   | Имя | Значение"
echo "     A     | @   | ${VPS_IP}"
echo "     A     | www | ${VPS_IP}"
echo
echo "  3. Подождать 10–30 мин, на VPS:"
echo "     cd /opt/pgbot && PRIMARY_DOMAIN=${RU_DOMAIN} bash scripts/setup-dual-domain.sh"
echo
echo "Проверка:"
echo "  dig +short ${RU_DOMAIN} A"
echo "  curl -sk https://${RU_DOMAIN}/health"
echo
echo "Если .ru тоже не открывается без VPN — IP в реестре РКН."
echo "Нужен отдельный VPS в РФ: bash scripts/selectel-bootstrap.sh"
echo "=============================================="

CURRENT=$(dig +short "${RU_DOMAIN}" A 2>/dev/null | head -1 || true)
if [ -n "$CURRENT" ]; then
  echo "Текущий A: ${CURRENT}"
  if [ "$CURRENT" = "$VPS_IP" ]; then
    echo "OK: DNS уже на VPS"
  else
    echo "WARN: DNS не на ${VPS_IP}"
  fi
fi

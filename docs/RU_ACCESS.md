# Доступ из России без VPN

## Почему не открывается

Сайт сейчас на **US VPS** `192.210.213.135` (`.xyz` домен, Porkbun).

Типичные причины блокировки в РФ:

1. **IP в реестре РКН** — на том же сервере крутится BetMasterAI (ставки). РКН блокирует **весь IP**, не только домен.
2. **Домен `.xyz`** — у части провайдеров фильтруют нестандартные зоны.
3. **US-хостинг** — реже полная блокировка, но в связке с п.1 — частая картина.

Починить только nginx или DNS на текущем IP **нельзя**, если IP уже в реестре.

## Что сделать (по приоритету)

### Вариант A — надёжно: отдельный VPS в России (рекомендуется)

| Шаг | Действие |
|-----|----------|
| 1 | VPS в **Selectel**, **Timeweb**, **Yandex Cloud** или **VK Cloud** (Москва/СПб), от ~500 ₽/мес |
| 2 | Домен **`pushkinskie-gory.ru`** — A-запись `@` и `www` → **новый RU IP** |
| 3 | На RU VPS: `bash scripts/selectel-bootstrap.sh` |
| 4 | VK Callback → `https://pushkinskie-gory.ru/api/v1/vk/callback` |
| 5 | BetMasterAI **оставить на US VPS** или перенести — PGBot не должен делить IP с gambling |

Скрипт: `scripts/selectel-bootstrap.sh`

### Вариант B — быстрая проверка: `.ru` на тот же IP

Если блокируют только **`.xyz`**, а не IP:

```bash
# DNS pushkinskie-gory.ru → 192.210.213.135
ssh root@192.210.213.135
cd /opt/pgbot && bash scripts/setup-dual-domain.sh
```

Пользователям давать ссылку **https://pushkinskie-gory.ru**

Если `.ru` тоже не открывается без VPN — нужен вариант A.

### Вариант C — не поможет надёжно

- Cloudflare перед US IP — многие CF-диапазоны в РФ режутся
- «Голый» IP вместо домена — тот же заблокированный IP

## Проверка

Из России (мобильный интернет без VPN):

```text
https://pushkinskie-gory.ru/health
https://pushkinskie-gory.xyz/health
```

Оба должны вернуть `{"status":"ok",...}`.

## Текущие домены в nginx

`scripts/setup-dual-domain.sh` поднимает:

- `pushkinskie-gory.xyz` + `www`
- `pushkinskie-gory.ru` + `www`

CORS и `PUBLIC_SITE_URL` — основной `.ru` после миграции, `.xyz` — зеркало.

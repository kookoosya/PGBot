# Cloudflare — доступ из России без VPN

**Домен:** `pushkinskie-gory.xyz` (Porkbun)  
**Origin (VPS):** `192.210.213.135` → nginx → docker `:8088`

Cloudflare проксирует трафик через свои IP — пользователь не ходит напрямую на US VPS. Так часто обходят блокировку IP/домена в РФ.

## 1. Cloudflare (бесплатный план)

1. [dash.cloudflare.com](https://dash.cloudflare.com) → **Add a site** → `pushkinskie-gory.xyz`
2. План **Free**
3. Cloudflare покажет **2 nameserver** (например `ada.ns.cloudflare.com`, `bob.ns.cloudflare.com`)

## 2. Porkbun — делегировать DNS на Cloudflare

1. [porkbun.com](https://porkbun.com) → домен `pushkinskie-gory.xyz`
2. **Authoritative Nameservers** → **Use custom nameservers**
3. Вставить NS от Cloudflare, сохранить
4. Удалить **URL Forwarding** / parking, если есть

Ожидание: 10 мин – 24 ч (обычно < 1 ч).

## 3. DNS в Cloudflare

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `192.210.213.135` | **Proxied** (оранжевое облако) |
| A | `www` | `192.210.213.135` | **Proxied** |

**Не** серые записи — только оранжевые (прокси).

## 4. SSL в Cloudflare

**SSL/TLS** → **Overview** → **Full (strict)**

На VPS уже есть Let's Encrypt для `pushkinskie-gory.xyz` (certbot). Origin должен отдавать валидный HTTPS.

**Edge Certificates:** Always Use HTTPS — **On**

## 5. VPS — nginx под Cloudflare

После делегирования NS на VPS:

```bash
ssh root@192.210.213.135
cd /opt/pgbot && git pull
bash scripts/setup-cloudflare-origin.sh
bash scripts/setup-primary-domain.sh
docker compose -f docker-compose.prod.yml restart nginx backend
```

Скрипт `setup-cloudflare-origin.sh`:
- доверяет IP Cloudflare для `real_ip`
- берёт реальный IP клиента из `CF-Connecting-IP`

## 6. Проверка из России (без VPN)

```text
https://pushkinskie-gory.xyz/health
```

Ответ: `{"status":"ok",...}`

## 7. VK Callback

После Cloudflare URL не меняется:

`https://pushkinskie-gory.xyz/api/v1/vk/callback`

## Если всё равно не открывается

- В Cloudflare **DNS** убедиться, что прокси **оранжевое**
- Попробовать **SSL/TLS → Full** (не strict) временно для диагностики
- Часть провайдеров режет Cloudflare — тогда только другой origin IP (RU VPS), без `.ru` домена

## Чего НЕ делаем

- Нет домена `.ru` — не используем
- Не переносим домен на Cloudflare Registrar — достаточно сменить NS в Porkbun

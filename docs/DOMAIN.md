# Домен портала

**Прод:** https://pushkinskie-gory.xyz

## DNS (Porkbun)

В панели домена **удалите** URL Forwarding / parking, затем добавьте:

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| A | `@` | `192.210.213.135` | 300 |
| A | `www` | `192.210.213.135` | 300 |

Проверка: `nslookup pushkinskie-gory.xyz` → `192.210.213.135`

После DNS (10–30 мин) на VPS автоматически при деплое:
- nginx → docker :8088
- certbot → HTTPS

## Деплой

```bash
ssh root@192.210.213.135
cd /opt/pgbot && git pull && bash scripts/setup-primary-domain.sh
docker compose -f docker-compose.prod.yml restart backend nginx
```

Или push в `main` → GitHub Actions **Deploy VPS** (нужен `VPS_PASSWORD` в Secrets).

## VK Callback

`https://pushkinskie-gory.xyz/api/v1/vk/callback`

## Старые URL (не использовать)

- `192-210-213-135.sslip.io` — резерв
- `pg.gmxreply.com` — семейство GMX, может блокироваться в РФ

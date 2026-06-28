# Домен портала

**Прод:** https://pushkinskie-gory.xyz  
**Доступ из РФ без VPN:** [CLOUDFLARE_SETUP_RU.md](./CLOUDFLARE_SETUP_RU.md) — **полная пошаговая инструкция**

## DNS сейчас (прямо на VPS)

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| A | `@` | `192.210.213.135` | 300 |
| A | `www` | `192.210.213.135` | 300 |

## После подключения Cloudflare

1. NS домена в Porkbun → nameservers Cloudflare (уже видно по IP `172.67.x` / `104.21.x`)
2. В Cloudflare DNS: A **`@`** и **`www`** → `192.210.213.135`, **Proxied** (не `api` — API по пути `/api/v1/`)
3. SSL: **Full (strict)**
4. На VPS: `bash scripts/setup-cloudflare-origin.sh` (уже выполняется при деплое)

## Деплой

Push в `main` → GitHub Actions **Deploy VPS**, или на сервере:

```bash
cd /opt/pgbot && git pull && bash scripts/vps-deploy.sh
```

## VK Callback

`https://pushkinskie-gory.xyz/api/v1/vk/callback`

## Старые URL (не использовать)

- `192-210-213-135.sslip.io`
- `pg.gmxreply.com`

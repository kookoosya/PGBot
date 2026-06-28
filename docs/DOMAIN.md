# Домен портала

**Прод:** https://pushkinskie-gory.xyz (международный)  
**Для РФ:** https://pushkinskie-gory.ru — см. [RU_ACCESS.md](./RU_ACCESS.md)

## DNS (Porkbun / reg.ru)

### pushkinskie-gory.xyz

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| A | `@` | `192.210.213.135` | 300 |
| A | `www` | `192.210.213.135` | 300 |

### pushkinskie-gory.ru (рекомендуется для жителей РФ)

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| A | `@` | **RU VPS IP** (или временно US IP для проверки) | 300 |
| A | `www` | тот же IP | 300 |

На VPS после DNS:

```bash
cd /opt/pgbot && git pull && bash scripts/setup-dual-domain.sh
```

Или push в `main` → GitHub Actions **Deploy VPS** (нужен `VPS_PASSWORD` в Secrets).

## VK Callback

`https://pushkinskie-gory.xyz/api/v1/vk/callback`

## Старые URL (не использовать)

- `192-210-213-135.sslip.io` — резерв
- `pg.gmxreply.com` — семейство GMX, может блокироваться в РФ

# Cloudflare — доступ из России (актуально 2026)

**Домен:** `pushkinskie-gory.xyz`  
**VPS:** `192.210.213.135`

> **Устарело:** оранжевое облако (Proxied) **не работает в РФ** с июня 2025.  
> Актуальная инструкция: [CLOUDFLARE_SETUP_RU.md](./CLOUDFLARE_SETUP_RU.md)

## Кратко

1. Cloudflare → **DNS** → записи `@` и `www` → **серое облако** (DNS only)
2. IP в записи: `192.210.213.135`
3. Проверка: `dig +short pushkinskie-gory.xyz A` → должен быть `192.210.213.135`, не `104.21.x`

Автоматически (агент): `CF_API_TOKEN` в `.deploy.env` → `node scripts/cloudflare-dns-only.mjs`

Подробно: [RU_ACCESS_FIX.md](./RU_ACCESS_FIX.md)

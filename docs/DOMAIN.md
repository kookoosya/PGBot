# Домен портала посёлка

**Основной адрес:** https://pushkiny.gmxreply.com ✅  
**Короткий:** https://pg.gmxreply.com ✅  
**Резерв:** http://192.210.213.135:8088

HTTPS включён (Let's Encrypt, автообновление).

Поддомен на `gmxreply.com` (Porkbun) — **без паспорта**, основной сайт GMX на Render не трогаем.

---

## DNS в Porkbun (2 записи)

1. https://porkbun.com → **Log In** → **Domain Management** → `gmxreply.com`
2. **DNS** → **Add**
3. Добавить:

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| A | `pushkiny` | `192.210.213.135` | 300 |
| A | `pg` | `192.210.213.135` | 300 |

**Не трогать** записи `www` и `@` — они ведут на Render (GMX).

Через 10–30 минут: **http://pushkiny.gmxreply.com**

---

## HTTPS (на VPS, после DNS)

```bash
ssh root@192.210.213.135
certbot --nginx -d pushkiny.gmxreply.com -d pg.gmxreply.com
```

---

## .рф домен (пушкинские-горы.рф)

Не обязателен. Timeweb требует паспорт для администратора — можно не использовать.

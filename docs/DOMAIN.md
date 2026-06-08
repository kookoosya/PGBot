# Домен портала посёлка

**Основной адрес:** https://pushkinskie-gory.ru  
**Резерв:** https://192-210-213-135.sslip.io

## DNS (обязательно для HTTPS)

В панели регистратора домена `pushkinskie-gory.ru` (registrant.ru / Timeweb / др.):

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| A | `@` | `192.210.213.135` | 300 |
| A | `www` | `192.210.213.135` | 300 |

После смены DNS подождите 10–30 минут и на VPS выполнится авто-выпуск сертификата при деплое (`scripts/setup-russia-mirror.sh`).

Проверка: `dig +short pushkinskie-gory.ru A` → должно быть `192.210.213.135`

## HTTPS

Let's Encrypt настраивается автоматически при деплое. Ручной запуск:

```bash
ssh root@192.210.213.135
certbot --nginx -d pushkinskie-gory.ru -d www.pushkinskie-gory.ru
```

## Старый домен

`pushkiny.gmxreply.com` — **не использовать в РФ** (блокировка семейства GMX в реестре РКН).

# Домен портала

**Текущий прод (канонический):** https://192-210-213-135.sslip.io  
**Домен pushkinskie-gory.ru:** отложен — DNS не настроен, в ссылках VK и smoke не используется.

Переменная `PUBLIC_SITE_URL` на VPS должна указывать на sslip.io (`scripts/setup-russia-mirror.sh` обновляет `.env` при деплое).

## Когда вернём .ru

В панели регистратора домена `pushkinskie-gory.ru`:

| Type | Host | Answer | TTL |
|------|------|--------|-----|
| A | `@` | `192.210.213.135` | 300 |
| A | `www` | `192.210.213.135` | 300 |

После смены DNS подождите 10–30 минут и на VPS выполнится авто-выпуск сертификата при деплое.

Проверка: `dig +short pushkinskie-gory.ru A` → должно быть `192.210.213.135`

```bash
ssh root@192.210.213.135
certbot --nginx -d pushkinskie-gory.ru -d www.pushkinskie-gory.ru
```

Затем сменить `PUBLIC_SITE_URL` и фронтовый `PRIMARY_SITE_URL` на `.ru`.

## Старый домен

`pushkiny.gmxreply.com` — **не использовать в РФ** (блокировка семейства GMX в реестре РКН).

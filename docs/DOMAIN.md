# Как привязать домен к сайту

Сайт сейчас: **http://192.210.213.135:8088**

## Если домен уже занят другим сайтом (как gmxreply.com на Render)

**Не трогайте основной домен** — `www.gmxreply.com` остаётся на Render (проект GMX).

Для «Народного Контроля» используйте **поддомен**, например:
- `nk.gmxreply.com` — рекомендуемый
- `pushkiny.gmxreply.com` — альтернатива

На VPS nginx уже подготовлен для этих имён (прокси на порт 8088).

BetMasterAI на том же VPS работает отдельно (порт 80) — конфликта не будет.

### DNS для gmxreply.com (домен на Render)

1. Откройте, **где управляется DNS** домена `gmxreply.com`:
   - панель регистратора (reg.ru, nic.ru и т.д.), или
   - Cloudflare, если домен там.
2. **Не меняйте** записи `www` / `@`, которые ведут на Render.
3. Добавьте **новую** A-запись:

| Тип | Имя (Host) | Значение |
|-----|------------|----------|
| A | `nk` | `192.210.213.135` |

Через 10–60 минут откроется: **http://nk.gmxreply.com**

4. HTTPS на VPS:
```bash
ssh root@192.210.213.135
apt install -y certbot python3-certbot-nginx
certbot --nginx -d nk.gmxreply.com
```

5. В `/opt/pgbot/.env` добавьте в CORS:
```
CORS_ORIGINS=https://nk.gmxreply.com,http://192.210.213.135:8088
```
```bash
cd /opt/pgbot && docker compose -f docker-compose.prod.yml restart backend
```

---

## Шаг 1. Купить домен (если нужен отдельный)

Регистраторы: [reg.ru](https://reg.ru), [nic.ru](https://nic.ru), [timeweb](https://timeweb.com).

Примеры имён:
- `narodny-kontrol-pg.ru`
- `nk-pushgory.ru`
- `kontrol-pg.ru`

---

## Шаг 2. DNS-записи

В панели регистратора добавьте **A-запись**:

| Тип | Имя | Значение |
|-----|-----|----------|
| A | `@` | `192.210.213.135` |
| A | `www` | `192.210.213.135` |

Подождите 10–60 минут (иногда до 24 ч), пока DNS обновится.

Проверка:
```bash
ping ваш-домен.ru
```

---

## Шаг 3. Nginx на VPS (отдельный поддомен или домен)

Подключитесь к VPS:
```bash
ssh root@192.210.213.135
```

Создайте конфиг (замените `ваш-домен.ru`):

```bash
cat > /etc/nginx/sites-available/pgbot << 'EOF'
server {
    listen 80;
    server_name ваш-домен.ru www.ваш-домен.ru;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/pgbot /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

> Если на VPS уже стоит системный nginx для BetMasterAI — этот конфиг добавит **второй** `server_name`, не трогая торгового бота.

---

## Шаг 4. HTTPS (бесплатный сертификат)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d ваш-домен.ru -d www.ваш-домен.ru
```

Certbot сам настроит SSL и автообновление.

---

## Шаг 5. Обновить .env проекта

```bash
nano /opt/pgbot/.env
```

Добавьте домен в CORS:
```
CORS_ORIGINS=https://ваш-домен.ru,https://www.ваш-домен.ru,http://192.210.213.135:8088
```

Перезапуск:
```bash
cd /opt/pgbot && docker compose -f docker-compose.prod.yml up -d --build
```

---

## Итог

| Что | Адрес |
|-----|-------|
| Народный Контроль | `https://ваш-домен.ru` |
| BetMasterAI | свой домен / порт 80 |
| Админка | `https://ваш-домен.ru/admin/login` |

Если нужен поддомен вместо отдельного домена:
- `kontrol.ваш-домен.ru` → та же A-запись + `server_name kontrol.ваш-домен.ru`

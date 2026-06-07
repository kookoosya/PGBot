# Домен для портала посёлка

**Домен:** https://пушкинские-горы.рф (Timeweb)  
**Резерв:** http://192.210.213.135:8088

Punycode: `xn----ftbelakbxobufw4ewc.xn--p1ai`

## DNS в Timeweb (пушкинские-горы.рф)

1. https://hosting.timeweb.ru/domains → клик по домену
2. **«Нет администратора»** — заполните данные администратора домена (обязательно для .рф)
3. **DNS / Управление зоной** → добавить записи:

| Тип | Субдомен | Значение |
|-----|----------|----------|
| A | `@` | `192.210.213.135` |
| A | `www` | `192.210.213.135` |

4. Уберите парковку Timeweb, если домен ведёт на их заглушку
5. Подождите 10–60 минут

На VPS nginx уже настроен. После DNS — HTTPS:
```bash
ssh root@192.210.213.135
certbot --nginx -d xn----ftbelakbxobufw4ewc.xn--p1ai
```

---

## Рекомендуемые имена (архив)

| Домен | Смысл |
|-------|-------|
| `pushkinskie-gory.ru` | Прямо и понятно |
| `poselok-pg.ru` | Посёлок ПГ |
| `pgory.ru` | Короткий |
| `pushgory.ru` | Короткий вариант |

Купить: [reg.ru](https://reg.ru), [porkbun.com](https://porkbun.com), [nic.ru](https://nic.ru) — от ~200–500 ₽/год.

---

## Настройка DNS

В панели регистратора:

| Тип | Имя | Значение |
|-----|-----|----------|
| A | `@` | `192.210.213.135` |
| A | `www` | `192.210.213.135` |

Подождите 10–60 минут.

---

## Nginx на VPS

```bash
ssh root@192.210.213.135
```

Замените `ваш-домен.ru` на купленный домен:

```bash
cat > /etc/nginx/sites-available/pgbot << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name ваш-домен.ru www.ваш-домен.ru;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8088;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
ln -sf /etc/nginx/sites-available/pgbot /etc/nginx/sites-enabled/pgbot
nginx -t && systemctl reload nginx
```

HTTPS:
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d ваш-домен.ru -d www.ваш-домен.ru
```

---

## .env проекта

```bash
nano /opt/pgbot/.env
```

```
CORS_ORIGINS=https://ваш-домен.ru,https://www.ваш-домен.ru,http://192.210.213.135:8088
```

```bash
cd /opt/pgbot && docker compose -f docker-compose.prod.yml restart backend
```

---

## Итог

| Проект | Где |
|--------|-----|
| **Портал посёлка Пушкинские Горы** | VPS, свой домен |
| BetMasterAI | VPS :80 (не трогать) |
| Другие личные сайты | Render / другие серверы |

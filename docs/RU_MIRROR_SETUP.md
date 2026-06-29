# Зеркало для доступа из России

**Симптом:** Cloudflare на **сером облаке** (DNS only), DNS → `192.210.213.135`, но сайт **без VPN не открывается**.

**Причина:** US-IP хостинга (RackNerd) **режут или не маршрутизируют** многие российские провайдеры (ТСПУ/DPI). Это не РКН по домену и не Cloudflare.

**Решение:** маленький **VPS в России** (~200–400 ₽/мес) как reverse-proxy перед US-origin.

---

## Шаг 1. Арендовать RU-VPS

Подойдёт любой Ubuntu 22.04 в РФ:

- [Timeweb Cloud](https://timeweb.cloud)
- [Selectel](https://selectel.ru)
- [Beget VPS](https://beget.com)
- [RuVDS](https://ruvds.com)

Минимум: 1 vCPU, 1 GB RAM, публичный IPv4.

---

## Шаг 2. Установить прокси на RU-VPS

```bash
ssh root@ВАШ_RU_IP
git clone https://github.com/kookoosya/PGBot.git /opt/pgbot-mirror
cd /opt/pgbot-mirror
bash scripts/setup-ru-reverse-proxy.sh
```

Скрипт поднимет nginx + Let's Encrypt и проксирует на `192.210.213.135`.

**Важно:** на момент certbot DNS домена должен уже указывать на **RU-IP** (шаг 3 можно сделать заранее).

---

## Шаг 3. Cloudflare DNS

**DNS → Records** (серое облако):

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `ВАШ_RU_IP` | DNS only |
| A | `www` | `ВАШ_RU_IP` | DNS only |

US-IP `192.210.213.135` в DNS **больше не нужен** — origin остаётся там, пользователи ходят на RU-прокси.

---

## Шаг 4. Проверка

С телефона **без VPN**:

- https://pushkinskie-gory.xyz
- https://pushkinskie-gory.xyz/health → `{"status":"ok",...}`

---

## Для агента

Если есть `RU_VPS_HOST` + `RU_VPS_PASSWORD` в `.deploy.env`:

```bash
# TODO: agent-deploy-ru-proxy.mjs
```

Пока RU-VPS нет в секретах — пользователь арендует VPS и передаёт root-доступ агенту.

---

## Альтернативы (хуже)

| Вариант | Почему не подходит |
|---------|-------------------|
| Cloudflare Proxied (оранжевое) | Режут в РФ с 06.2025 |
| Только US-IP в DNS | Режут IP |
| VPN для жителей | Не подходит для портала |

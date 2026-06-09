# Развёртывание

## Требования

- Docker и Docker Compose
- Ubuntu 22.04 (рекомендуется)
- Домен с HTTPS (для production)

## Быстрый старт

```bash
cp .env.example .env
# Отредактируйте .env — укажите API-ключи

docker compose up -d --build
```

Сервисы:
- **Админ-панель**: http://localhost (через nginx)
- **API**: http://localhost/api/v1
- **Swagger**: http://localhost/api/docs
- **Frontend напрямую**: http://localhost:3000

Логин по умолчанию: `admin` / пароль из `SUPER_ADMIN_PASSWORD`.

## Настройка VK Bot

1. Создайте сообщество ВКонтакте
2. Управление → Работа с API → Callback API
3. URL: `https://your-domain.com/api/v1/vk/callback`
4. Скопируйте код подтверждения в `VK_CONFIRMATION_CODE`
5. Создайте ключ доступа сообщества → `VK_GROUP_TOKEN`
6. Включите событие `message_new`

## Настройка Telegram

1. Создайте бота через @BotFather
2. Получите `TELEGRAM_BOT_TOKEN`
3. Узнайте chat_id (через @userinfobot) → `TELEGRAM_ADMIN_CHAT_ID`

## Настройка Gemini

1. Получите API-ключ: https://aistudio.google.com/apikey
2. Укажите в `GEMINI_API_KEY`

## Production

- Используйте HTTPS (Let's Encrypt + certbot)
- Смените `SECRET_KEY` и пароли
- Настройте бэкапы PostgreSQL
- Ограничьте доступ к порту 5432

## Миграции

```bash
docker compose exec backend alembic upgrade head
```

## Seed

```bash
docker compose exec backend python /app/../scripts/seed_db.py
```

# Пушкинские Горы — портал посёлка

Публичный портал посёлка Пушкинские Горы (Псковская область): афиша, объявления, карта, обращения жителей, VK-бот и VK Mini App.

**Прод:** https://192-210-213-135.sslip.io

## Возможности

| Модуль | Описание |
|--------|----------|
| **Обращения** | Приём через сайт и VK-бот; AI-анализ (Gemini), дедупликация, назначение отделов |
| **Афиша** | 13 внешних источников: VK, Kudago, кинотеатры Пскова, Пушкинский заповедник и др. |
| **Объявления / работа** | Доска с модерацией, квоты, оплата переводом |
| **Карта** | Места, маршруты, такси, офлайн-тайлы (PWA) |
| **Услуги** | Регистрация мастеров, запись, кабинет провайдера |
| **ИИ-помощник** | `/ai` — **30** бесплатных сообщений/день |
| **VK-бот** | Меню, пошаговые сценарии, digest, модерация |
| **VK Mini App** | `/vk/*` — компактная оболочка внутри ВКонтакте |
| **Админка** | `/admin` — обращения, аналитика, модерация, аудит |

## Стек

| Компонент | Технологии |
|-----------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Frontend | React 18, Vite 6, TypeScript, Tailwind CSS |
| Database | PostgreSQL 16 |
| Cache (prod) | Redis 7 |
| AI | Gemini, Pollinations, OpenRouter |
| Infra | Docker Compose, Nginx, GitHub Actions |

## Быстрый старт

```bash
cp .env.example .env
# Заполните API-ключи в .env

docker compose up -d --build
```

- Сайт: http://localhost
- API: http://localhost/api/docs
- Админка: http://localhost/admin — логин `admin`, пароль из `SUPER_ADMIN_PASSWORD`

## Структура

```
backend/          # FastAPI
frontend/         # React SPA
shared/           # portal_copy.json — единые тексты
docker/           # Nginx
docs/             # Документация
scripts/          # Деплой, smoke, cron
```

## Тесты

```bash
cd backend && python3 -m pytest -q -m "not postgres"
cd frontend && npm run test && npm run build
bash scripts/smoke-public.sh http://localhost
```

## Документация

- [Архитектура](docs/ARCHITECTURE.md)
- [Развёртывание](docs/DEPLOYMENT.md)
- [Настройка VK](docs/VK_SETUP.md)
- [Настройка AI](docs/AI_SETUP.md)
- [Статус рефакторинга](docs/REFACTOR_STATUS.md)
- [Дорожная карта](docs/ROADMAP.md)

## Лицензия

MIT

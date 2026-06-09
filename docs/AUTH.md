# Аутентификация (JWT + httpOnly refresh cookie)

## Схема

- **Access token** — короткоживущий JWT (по умолчанию 30 мин), хранится **только в памяти** фронтенда и передаётся в `Authorization: Bearer`.
- **Refresh token** — случайная строка в **httpOnly cookie** (`pg_refresh_user` / `pg_refresh_admin`), хэш хранится в PostgreSQL.
- При истечении access token фронтенд вызывает `POST /api/v1/auth/refresh?client=user|admin` с `credentials: include`.
- При logout — `POST /api/v1/auth/logout?client=...`, cookie удаляется, refresh отзывается в БД.

## Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/auth/login?client=user\|admin` | Access token в JSON + refresh cookie |
| POST | `/auth/refresh?client=...` | Новый access token, ротация refresh |
| POST | `/auth/logout?client=...` | Отзыв refresh + очистка cookie |

Refresh/logout требуют заголовок `X-Requested-With: XMLHttpRequest` (базовая CSRF-защита).

## Cookie

- `HttpOnly`, `Secure` (в production), `SameSite=Lax`
- Path: `/api/v1/auth`

## Переменные окружения

```env
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14
```

## Миграция с localStorage

После деплоя пользователям потребуется **один повторный вход**: старые токены из localStorage больше не используются. Refresh cookie появляется только после успешного login.

## Миграция БД

```bash
cd backend && alembic upgrade head
```

Создаёт таблицу `refresh_tokens` (revision `016`).

# План рефакторинга и качества кода

Обновлено: ветка `cursor/code-quality-771b` (база: `cursor/refactor-main-py-771b`).

**Pro / ИИ / оплаты — отложены.** Ниже — что реально важно для всего портала.

---

## Что уже сделано в этой ветке

| Что | Где |
|-----|-----|
| Ruff (lint + format) | `backend/pyproject.toml`, `make backend-lint` |
| Pytest (базовые тесты) | `backend/tests/` |
| pip-audit в CI | `.github/workflows/ci.yml` |
| ESLint для frontend | `frontend/eslint.config.js`, `npm run lint` |
| Alembic upgrade в CI | CI job backend |
| pre-commit | `.pre-commit-config.yaml` |
| Makefile | `make check` — всё разом |
| Prod: 1 worker uvicorn | `docker-compose.prod.yml` — VK flows в памяти не ломаются |
| Удалён дубликат seed | остался только `backend/scripts/seed_db.py` |

Запуск локально:

```bash
make install-dev
make check
pre-commit install   # опционально
```

---

## P0 — срочно, иначе прод ломается или теряет деньги

### 1. VK multi-step flows в памяти
**Файл:** `backend/app/services/vk_flows.py` — `_flows: dict[...]`

При `--workers 2` (было в prod) пользователь начинает объявление в одном процессе, ответ уходит в другой — flow теряется.

**Сделано:** workers=1 в prod.  
**Доработать:** хранить flow в PostgreSQL (как `VkAiSession`), или Redis.

**Объём:** средний (1–2 дня).

### 2. Нет автотестов на критичные сценарии
Сейчас 4 файла unit-тестов. Нет проверок: auth JWT, ACL жалоб, classified antifraud end-to-end, VK webhook.

**Доработать:** pytest + httpx `AsyncClient` для `/auth/login`, `/issues`, `/classifieds`.

**Объём:** большой (постепенно, по 5–10 тестов за итерацию).

### 3. Деплой feature-веток на один VPS
На сервере гонялись `cursor/ai-tiers`, `cursor/bank-auto-pro`, `cursor/refactor-*` — прод непредсказуем.

**Доработать:**
- prod только из `main`
- feature → staging или manual workflow_dispatch
- `.github/workflows/deploy.yml` — убрать hardcoded IP в пользу secrets

**Объём:** малый (полдня).

### 4. JWT в localStorage (frontend)
**Файлы:** `frontend/src/lib/auth.tsx`, `userAuth.tsx`

XSS = угон сессии.

**Доработать:** httpOnly cookie + refresh, или короткий TTL + rotation.

**Объём:** большой (архитектурно).

---

## P1 — важно, качество и поддержка

### 5. `frontend/src/lib/api.ts` (~815 строк)
107 методов + типы в одном файле. Любая фича = конфликты merge.

**Доработать:** разбить на `api/client.ts`, `api/issues.ts`, `api/places.ts`, `types/*.ts`. Или codegen из OpenAPI.

**Объём:** большой.

### 6. God-модули backend (400–800+ строк)
| Файл | Строк | Содержимое |
|------|-------|------------|
| `classified_service.py` | ~770 | объявления + оплата + модерация |
| `place_service.py` | ~790 | карта + отзывы + жалобы |
| `issue_service.py` | ~830 | жалобы + ACL + поиск |
| `vk_webhook.py` | ~490 | весь VK в одном роутере |
| `vk_flows.py` | ~370 | многошаговые сценарии |

**Доработать:** router → handler → service по доменам. VK вынести в `vk/handlers/`.

**Объём:** большой (по одному модулю за спринт).

### 7. Rate limit in-memory (SlowAPI)
**Файл:** `backend/app/core/rate_limit.py`

При рестарте и нескольких workers лимиты не общие.

**Доработать:** Redis backend для SlowAPI в prod.

**Объём:** средний.

### 8. Двойной commit pattern
**Файл:** `backend/app/database.py` — `get_db()` auto-commit + ручные `db.commit()` в handlers.

Риск: половина commit, половина rollback неочевидна.

**Доработать:** один стиль — commit только в services или только в dependency.

**Объём:** средний.

### 9. CI был smoke-only
**Было:** `python -c "from app.main import app"`.  
**Стало:** ruff + pytest + alembic + eslint + build + pip-audit.

**Доработать:** coverage gate (например ≥40% на `app/core`, `app/services/classified_antifraud`).

**Объём:** малый.

### 10. Документация устарела
`README.md`, `docs/ARCHITECTURE.md` — MVP 2024, не отражают карту, объявления, VK bot, кабинет.

**Доработать:** один `docs/ARCHITECTURE.md` актуальный + схема модулей.

**Объём:** малый.

---

## P2 — улучшения, не горит

### 11. Разветвление веток с AI/оплатами
Ветки `cursor/ai-tiers-771b`, `cursor/bank-auto-pro-771b` — +82 коммита, migrations 015–025, YooKassa + bank IMAP + entitlements.

**Не мержить в prod**, пока не frozen scope ИИ.

**Когда вернётесь:** один payment provider interface, тесты на grant entitlement.

### 12. Events subsystem (есть в ai-tiers, нет в refactor-main)
8 источников, sync на deploy, KudaGo «pskov» не работает — ошибки в логах норм.

**Доработать:** вынести sync из deploy в cron; мониторинг `EventSyncResult.errors`.

### 13. Frontend god-pages
| Страница | Строк |
|----------|-------|
| `Map.tsx` | ~734 |
| `AIChat.tsx` | ~250 (на refactor ветке проще) |

Hooks + subcomponents.

### 14. TypeScript дубли типов
`PublicEvent` / `EventItem` и др. в `api.ts` — слить.

### 15. Telegram notifications
Fire-and-forget, без retry queue.

### 16. Classified payment fields в БД, но `requires_payment: False`
Мёртвый код в `classifieds.py` — удалить или включить продуктово.

---

## P3 — косметика и долгий хвост

- Backward-compat shims (`datetime_utils.py` → `app.utils.datetime`)
- `enums.py` 286 строк — labels в отдельный модуль
- Storybook / component tests (Vitest)
- `.dockerignore` для меньших образов
- Dependabot для npm/pip
- CSRF — актуально только при переходе на cookie-auth

---

## Рекомендуемый порядок работ (без Pro/ИИ)

```
Неделя 1 (P0)
├── Зафиксировать deploy только main
├── Добавить 10–15 API тестов (auth, issues, classifieds)
└── VK flows → DB (или оставить workers=1 + мониторинг)

Неделя 2 (P1)
├── Разбить api.ts (issues + places + classifieds)
├── ruff fix по всему backend (авто)
└── Обновить ARCHITECTURE.md

Неделя 3–4 (P1)
├── Разбить vk_webhook.py на handlers
├── Redis rate limit
└── Единый db.commit pattern

Потом (P2)
├── Решить судьбу ai-tiers branch отдельным PR
├── Map.tsx refactor
└── Events sync out of deploy
```

---

## Метрики «здоровья» (целевые)

| Метрика | Сейчас | Цель |
|---------|--------|------|
| pytest tests | ~10 | 80+ |
| CI steps | 8 | + coverage |
| Max file size (backend) | ~830 lines | <400 |
| api.ts | ~815 lines | <200 + modules |
| Prod workers | 1 (fix) | 2 после Redis flows |
| Deploy branch | хаос | main only |

---

## Честный итог

Код **рабочий и feature-complete** для посёлка, но вырос **быстрее дисциплины**: нет тестов, god-файлы, параллельные ветки с оплатами/ИИ, VK state in-memory.

**Не трогать сейчас:** Pro, YooKassa, bank IMAP, entitlements — отдельная ветка, отдельный PR когда созреет.

**Трогать сейчас:** CI, тесты, deploy discipline, VK flows, разрезание api.ts и vk_webhook.

Вопросы — в issue или сразу задача агенту: «начни с P0 пункт 3» / «разбей api.ts».

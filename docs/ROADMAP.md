# Дорожная карта: рефакторинг, VK-бот, VK Mini App

**Текущий прод:** https://192-210-213-135.sslip.io  
**Домен pushkinskie-gory.ru:** отложен (DNS не используется).

---

## Фаза 0 — Стабильность (сейчас)

| # | Задача | Зачем | Файлы |
|---|--------|-------|-------|
| 0.1 | Канонический URL = sslip.io | VK deep links, smoke, уведомления | `setup-russia-mirror.sh`, `config.py`, `siteUrl.ts` |
| 0.2 | Один uvicorn worker (временно) | VK flows и AI mode в RAM — ломаются при 2 workers | `docker-compose.prod.yml` |
| 0.3 | Smoke/deploy только на sslip.io | Не ссылаться на .ru в CI и deploy | `remote-deploy.sh`, `MERGE_PLAN.md` |

**Следующий шаг после 0.2:** перенести `vk_flows._flows` и `ai_mode._ai_peers` в PostgreSQL (как уже сделано для `vk_ai_sessions`).

---

## Фаза 1 — Рефакторинг backend (без смены поведения)

### 1.1 VK-модули (приоритет: бот + будущее приложение)

```
backend/app/services/vk/
├── client.py          ← app/services/vk.py
├── bot.py
├── flows.py           ← с персистенцией в БД
├── command_router/    ← разбить vk_command_router.py (~800 строк)
│   ├── menu.py
│   ├── map_keywords.py
│   ├── ai.py
│   ├── complaints.py
│   └── weather.py
├── messages.py
├── moderation.py
└── digest.py
```

| Задача | Объём |
|--------|-------|
| Персистенция flows (peer_id, kind, step, data JSON) | Средний |
| Персистенция AI mode в БД или Redis | Малый |
| Объявление из VK → `create_classified_ad()` (единая валидация) | Средний |
| Единый источник статусов/эмодзи | `portal_copy.py` только | Малый |

### 1.2 «Божественные» сервисы

| Файл | Строк | Разбить на |
|------|-------|------------|
| `classified_service.py` | ~900 | search, create, moderation, notify |
| `place_service.py` | ~900 | crud, map, reviews, sync |
| `issue_service.py` | ~800 | search, status, comments, official |
| `issue_processor.py` | ~540 | оставить ingest; lifecycle в issue_service |

### 1.3 API и тесты

- Покрыть: auth, classifieds create/moderate, issue lifecycle, VK webhook (mock)
- Цель: **50+** интеграционных тестов на критические пути
- Frontend: **0 тестов сейчас** → Vitest на `eventUtils`, `literaryCopy`, API hooks (фаза 1b)

---

## Фаза 2 — Рефакторинг frontend

| # | Задача | Файлы |
|---|--------|-------|
| 2.1 | Разбить `api.ts` (~1100 строк) | `lib/api/{auth,classifieds,issues,events,admin}.ts` |
| 2.2 | Разбить `Map.tsx` (~850 строк) | `pages/map/*`, hooks |
| 2.3 | URL сайта из `/public/info` | убрать хардкод в `siteUrl.ts` |
| 2.4 | Синхронизация текстов | `portal_copy.py` ↔ `literaryCopy.ts` (JSON или codegen) |

---

## Фаза 3 — VK Mini App (приложение ВКонтакте)

Сейчас есть только **Callback-бот**. Mini App — отдельный клиент в iframe VK.

### 3.1 Инфраструктура

- Регистрация приложения VK (App ID, secure key)
- `VK_APP_ID`, `VK_APP_SECRET` в `config.py`
- CORS: `https://vk.com`, `https://*.vk.com`
- CSP / `X-Frame-Options`: разрешить `frame-ancestors` для VK (сейчас `DENY` везде)

### 3.2 Backend

- `POST /api/v1/vk/auth` — обмен launch params / silent token → JWT
- Привязка `users.vk_id` (поле уже есть)
- Переиспользование public API: events, classifieds, issues, cabinet

### 3.3 Frontend

- `@vkontakte/vk-bridge` — `VKWebAppInit`, launch params
- Маршрут `/vk` или отдельный entry: компактная оболочка
- Экраны MVP: афиша, объявления, обращение, мои заявки
- Автовход по VK ID (без пароля)

### 3.4 Бот + приложение вместе

| Сценарий | Бот | Mini App |
|----------|-----|----------|
| Афиша | Команда + deep link | Нативный экран |
| Объявление | 4 шага в чате | Форма в iframe |
| Обращение | Текст/фото | Форма + статусы |
| Статусы | «Мои обращения» | Тот же API + UI |

Deep links бота ведут на **sslip.io** (или в Mini App через `vk.com/app{id}`).

---

## Фаза 4 — Продукт (после стабилизации)

- Закрыть черновые PR (#20–#28): Redis rate limit, JWT cookies — по необходимости
- VK Pay для платных объявлений (если вернётся монетизация)
- Push-уведомления в Mini App
- Офлайн-карта, PWA

---

## Что уже сделано (main)

- Стиль «Пушкиногорский альбом»
- VK deep links, кабинет, фильтры обращений, post-submit
- Smoke 23+ проверок, pytest ~20 unit/integration
- Cron синхронизации афиши, cinema filter
- Map polish (#30), literary cohesion (#37)

## Черновые PR (не мержить без ревью)

#20 code-quality, #21 JWT cookies, #24–#28 рефакторинги сервисов, #29 restore-landing — устарели или конфликтуют с main.

---

## Рекомендуемый порядок работ

1. **Фаза 0** — sslip + workers (этот PR)
2. **VK flows в БД** — надёжный бот на prod
3. **Фаза 1.1** — структура `services/vk/`
4. **Фаза 2.1** — split `api.ts`
5. **Фаза 3 MVP** — auth + Bridge + 3 экрана Mini App
6. **Фаза 1.2** — god services по мере роста команды

Оценка объёма фаз 1–3: **крупный проект** (десятки модулей, новая auth-ветка, iframe-политики). Делать итерациями с деплоем после каждой фазы.

# Дорожная карта: рефакторинг, VK-бот, VK Mini App

**Текущий прод:** https://192-210-213-135.sslip.io  
**Домен pushkinskie-gory.ru:** отложен (DNS не используется).

---

## Фаза 0 — Стабильность (сейчас)

| # | Задача | Зачем | Файлы |
|---|--------|-------|-------|
| 0.1 | Канонический URL = sslip.io | VK deep links, smoke, уведомления | `setup-russia-mirror.sh`, `config.py`, `siteUrl.ts` |
| 0.2 | ~~Один uvicorn worker (временно)~~ | VK flows и AI mode перенесены в PostgreSQL — можно 2 workers | `docker-compose.prod.yml` |
| 0.2b | **VK flows в PostgreSQL** | ✅ сделано | `vk_flow_store.py`, миграция 020 |
| 0.2c | **AI mode в PostgreSQL** | ✅ сделано | `vk_ai_mode_store.py`, миграция 021 |
| 0.3 | Smoke/deploy только на sslip.io | Не ссылаться на .ru в CI и deploy | `remote-deploy.sh`, `MERGE_PLAN.md` |

**Следующий шаг:** объединить объявления VK с `create_classified_ad()`; перенести `vk_bot`, `vk_digest` в пакет `vk/`.

---

## Фаза 1 — Рефакторинг backend (без смены поведения)

### 1.1 VK-модули (приоритет: бот + будущее приложение)

```
backend/app/services/vk/
├── __init__.py         # VK API client (без циклических импортов)
├── client.py           # send_message, keyboards, parse_vk_message
├── context.py          # VkRouteContext
├── command_router.py   # публичный API маршрутизации (тонкий)
├── message_handler.py  # route_welcome, route_vk_message, route_complaint
├── commands.py         # handle_* + COMMAND_ALIASES
├── ai_handler.py       # route_ai_message, route_free_chat
├── ai_mode.py          # enter/exit/is AI mode (PostgreSQL)
├── flows.py            # многошаговые сценарии
├── flow_store.py       # персистенция flows
├── helpers.py          # ответы, карта, такси
├── bot.py              # подписки, список объявлений
├── digest.py           # ежедневная сводка
├── moderation.py       # антиспам, баны
├── subscription.py     # пресеты подписок
├── ai_history.py       # история ИИ-диалога в БД
└── voice.py            # распознавание голосовых
```

| Задача | Объём |
|--------|-------|
| Персистенция flows (peer_id, kind, step, data JSON) | ✅ `vk/flows.py`, `vk/flow_store.py` |
| Персистенция AI mode в БД | ✅ `vk/ai_mode.py` |
| Структура `services/vk/` + разбиение router | ✅ `commands.py`, `message_handler.py`, `ai_handler.py` |
| Объявление из VK → `create_classified_ad()` (единая валидация) | ✅ `create_classified_ad_from_vk` |
| Перенос `vk_bot`, `vk_digest`, moderation в `vk/` | ✅ `bot.py`, `digest.py`, `moderation.py` |
| Импорты webhook/admin → `services/vk/` напрямую | ✅ |
| Удалить мёртвые VK shims (`vk_bot`, `vk_subscription`, …) | ✅ |
| Единый источник статусов/эмодзи | `portal_copy.py` только | Малый |

### 1.2 «Божественные» сервисы

| Файл | Строк | Разбить на |
|------|-------|------------|
| `classified_service.py` | ~900 | ✅ split → `classified/` package |
| `place_service.py` | ~900 | crud, map, reviews, sync |
| `issue_service.py` | ~800 | search, status, comments, official |
| `issue_processor.py` | ~540 | оставить ingest; lifecycle в issue_service |

### 1.3 API и тесты

- Покрыть: auth, classifieds create/moderate, issue lifecycle, VK webhook (mock)
- Цель: **50+** интеграционных тестов на критические пути
- Frontend: **Vitest 13** → hooks, API client (фаза 1b)

---

## Фаза 2 — Рефакторинг frontend

| # | Задача | Файлы |
|---|--------|-------|
| 2.1 | Разбить `api.ts` (~1100 строк) | ✅ `lib/api/*` |
| 2.2 | Разбить `Map.tsx` (~850 строк) | ✅ `pages/map/*` |
| 2.3 | URL сайта из `/public/info` | ✅ `useSiteInfo` |
| 2.4 | Синхронизация текстов | ✅ `shared/portal_copy.json` |
| 2.5 | Vitest на утилиты | ✅ `eventUtils`, `literaryCopy`, `eventRegionFilters` |
| 2.6 | Удалить мёртвые компоненты | ✅ QuickNav, verses, gallery, … |

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

- Стиль «Пушкиногорский альбом», nav dedup, footer, PageHeader contrast
- VK deep links, кабинет, фильтры обращений, post-submit
- **Smoke 26** проверок, **pytest ~99**, **Vitest 13**
- Cron синхронизации афиши, cinema filter, events city row (кино + Псков сверху)
- Backend packages: `issue/`, `place/`, `classified/`, `vk/`, `event_sources/`
- Frontend split: `lib/api/*`, `pages/map/*`, `useSiteInfo`
- `shared/portal_copy.json`, единые `filter-chip` и `literary-card`
- Подробный статус: **`docs/REFACTOR_STATUS.md`**

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

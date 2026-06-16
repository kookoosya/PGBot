# Архитектура портала Пушкинские Горы

Публичный портал посёлка с VK-ботом, афишей, объявлениями, картой и обращениями жителей. Визуальный стиль публичной части — **«Пушкиногорский альбом»** (литературные тексты, тёплая палитра, шрифты Playfair Display + Source Sans 3).

## Обзор системы

```
Житель / гость
    ├── Сайт (React SPA) ──► FastAPI /api/v1 ──► PostgreSQL
    ├── VK-бот ──► VK Callback ──► Issue / Classified flows
    └── Telegram (уведомления владельцу)

Внешние источники афиши: VK, Kudago, TimePad, Orbilet, ProCulture, кинотеатры Пскова
Фоновые задачи: синхронизация событий (cron), обогащение кино, дедупликация
```

## Backend (FastAPI)

| Модуль | Назначение |
|--------|------------|
| `app/api/v1/public_info.py` | Публичные эндпоинты: `/public/today`, `/public/events`, `/public/info` |
| `app/api/v1/classifieds.py` | Доска объявлений (список, создание, модерация) |
| `app/api/v1/issues.py` | Обращения жителей (сайт + антиспам) |
| `app/api/v1/vk_webhook.py` | VK Callback API |
| `app/services/vk_command_router.py` | Маршрутизация команд VK-бота |
| `app/services/vk_flows.py` | Пошаговые сценарии: объявление, пожелание, ошибка карты |
| `app/services/issue_processor.py` | AI-анализ, дедупликация обращений, уведомления |
| `app/services/classified_service.py` | Объявления: валидация, модерация, VK-уведомления |
| `app/services/event_service.py` | Публичная афиша, фильтр кино |
| `app/services/event_dedupe_service.py` | Дедупликация событий в ленте |
| `app/services/cinema_enrichment.py` | Фильтр «реальных» фильмов vs культурные события |
| `app/services/event_sources/` | Синхронизация внешних источников афиши |
| `app/constants/portal_copy.py` | Тексты VK в едином тоне с фронтендом |

### Публичные API

- `GET /api/v1/public/today` — снимок для главной: погода, афиша, объявление дня, статистика карты
- `GET /api/v1/public/events` — список событий (`region`, `search`)
- `GET /api/v1/public/events/{id}` — карточка события
- `GET /api/v1/classifieds` — доска объявлений
- `GET /health` — проверка живости

## Frontend (React + Vite)

### Публичные страницы

| Путь | Компонент | Описание |
|------|-----------|----------|
| `/` | `Landing.tsx` | Главная, блок «Сегодня в посёлке» |
| `/events` | `EventsPage.tsx` | Афиша (посёлок + Псков + кино) |
| `/classifieds` | `Classifieds.tsx` | Объявления; `?new=1` — открыть форму |
| `/complaints` | `Complaints.tsx` | Обращения; `?issue={id}` — подсветка заявки |
| `/cabinet` | `UserCabinet.tsx` | Личный кабинет жителя |
| `/map` | `Map.tsx` | Карта (маркеры, маршруты, такси) |

### Стиль «Пушкиногорский альбом»

- **Тексты:** `frontend/src/lib/literaryCopy.ts` — стихи, заголовки секций, пустые состояния
- **Стили:** `frontend/src/styles/portal/` — shell, map, landing epic, widgets; `styles/literary-album/` — карточки, панели, формы
- **Компоненты:** `frontend/src/components/literary/` — `LiterarySectionHead`, `LiteraryEmptyState`, loaders
- **Удобство:** класс `.literary-form-comfort` — крупные поля для пожилых пользователей

### Связь VK ↔ сайт

- Общие тексты: `portal_copy.py` ↔ `literaryCopy.ts`
- Deep links из VK: `/classifieds/{id}`, `/complaints?issue={id}`, `/events`, `/classifieds?new=1`
- Inline-кнопки: `get_inline_links_keyboard()` в `app/services/vk.py`

## VK-бот

Клавиатура меню: ИИ, карта, объявления, работа, услуги, афиша, подача объявления, обращения, такси, погода.

Свободный текст «аптека», «магазин» → справочник карты. Жалоба с фото → `issue_processor`. Команда «Мои обращения» → статусы с подсказками и ссылкой на портал.

## База данных (PostgreSQL)

Основные сущности: `users`, `issues`, `classified_ads`, `village_events`, `places`, `taxi_services`, `vk_subscribers`, `ai_analysis`, `audit_logs`.

## AI-анализ обращений (Gemini)

На каждое обращение возвращается JSON с категорией, приоритетом, summary и `duplicate_probability`. При недоступности Gemini — rule-based fallback.

## Дедупликация

### Обращения

Если `duplicate_probability > 0.80`, обращение связывается с существующим, счётчик подтверждений увеличивается.

### События афиши

`event_dedupe_key()` — нормализованный заголовок + время + регион + категория + площадка. При дублях сохраняется запись с лучшим источником (`orbilet` > `vk` > `kudago`).

### Кино

`is_real_cinema_event()` отсекает культурные мероприятия, попавшие в категорию cinema, и планетарий.

## Карта (интегрировано из PR #30)

- Золотые маркеры проверенных мест (`map-marker-ref`)
- Кластеризация и spiderfy
- Дедупликация OSM/Yandex рядом с эталонными точками (`place_cleanup.py`)
- Литературное оформление панелей маршрутов и такси (#37)

## Инфраструктура

| Компонент | Файл |
|-----------|------|
| Деплой | `scripts/remote-deploy.sh` |
| Smoke-тесты | `scripts/smoke-public.sh`, `scripts/smoke_check_cinema.py` |
| Cron синхронизации | `scripts/vps-sync-events.sh`, `scripts/install-vps-cron.sh` |
| CI | `.github/workflows/ci.yml` — build, pytest, smoke prod |
| Тесты | `backend/tests/` — cinema filter, event dedupe, public API |

## Роли пользователей

| Роль | Доступ |
|------|--------|
| Resident | Кабинет, объявления, обращения |
| Service provider | Кабинет мастера, запись |
| Administration / SocialService | Портал служб `/official` |
| SuperAdmin | Админ-панель `/admin` |

## Уведомления

- **VK** — автору объявления/обращения (модерация, смена статуса) с deep links
- **Telegram / VK admin** — владельцу портала (новые заявки, алерты кино)

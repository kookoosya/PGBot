# Статус рефакторинга портала Пушкинские Горы

**Прод:** https://192-210-213-135.sslip.io  
**Деплой:** `bash scripts/remote-deploy.sh` (пароль в `.deploy.env` или `VPS_PASSWORD`)  
**Обновлено:** 2026-06-16

---

## Сводка

| Область | Готово | В работе / осталось |
|---------|--------|---------------------|
| Инфра / деплой | sslip.io, smoke 26, cron афиши, 2 workers | DNS .ru отложен |
| Backend домены | `issue/`, `place/`, `classified/`, `provider/`, `event/`, `weather/`, `vk/`, `models/enums/` | — |
| Backend тесты | places, admin, feedback, visits, AI + postgres suite | — |
| Frontend CSS | `literary-album/` split (core, landing, pages) | `index.css` ~2800 строк |
| Frontend тесты | Vitest **58** + renderHook | компоненты |
| Тексты | `portal_copy.json`: brand, empty_states, **landing_hero** | PAGE_SECTIONS во frontend |
| VK Mini App | auth API, shell `/vk/*`, CSP frame-ancestors | прод App ID в VK |

---

## ✅ Сделано (main)

### Фаза 0 — стабильность
- Канонический URL: `192-210-213-135.sslip.io`
- VK flows и AI mode в PostgreSQL (миграции 020–021)
- Smoke 26 проверок на каждый деплой
- Cron: кино каждые 8ч, полная синхронизация в 03:15

### Фаза 1 — backend
- **`services/issue/`** — crud, status, comments, official, dedup; facade `issue_service.py`
- **`services/place/`** — crud, map, reviews, sync; facade `place_service.py`
- **`services/classified/`** — create, search, moderate; facade `classified_service.py`
- **`services/vk/`** — bot, flows, moderation, digest, AI, voice (17 модулей)
- **`services/event_sources/`** — адаптеры Kudago, VK, Orbilet, Kinopskov и др.
- VK объявления → `create_classified_ad_from_vk()` (единая валидация)
- `shared/portal_copy.json` ↔ backend `portal_copy.py`

### Фаза 2 — frontend
- **`lib/api/`** — client, types, auth, issues, classifieds, places, services, admin, ai, public, events
- **`pages/map/`** — useMapPage, layers, panels (Map.tsx ~194 строк)
- **`useSiteInfo`** — URL из `/api/v1/public/info`
- Literary polish: nav, footer, PageHeader contrast, portal copy
- Events: кино + Псков рядом сверху; source chip; trusted VK sources
- Единые `filter-chip` и `literary-card` на объявлениях/услугах
- Vitest: `eventUtils`, `literaryCopy`

---

## ⚠️ Лишнее / мёртвый код (удалять)

### Frontend — компоненты без импортов
| Файл | Причина |
|------|---------|
| `QuickNav.tsx` | заменён TabNav + LandingQuickNav |
| `PagePortalNav.tsx` | убран с inner pages |
| `PushkinBanner.tsx`, `PushkinVersesSection.tsx` | убраны стихи с продукта |
| `VillageGallery.tsx` | не используется |
| `SeasonalTip.tsx` + `seasonalTip.ts` | не используется |
| `LandingJobsPreview.tsx`, `LandingUsefulNearby.tsx` | landing перестроен |
| `WeatherWidgetDetailed.tsx` | не используется |

### Frontend — CSS
- ✅ `literary-album.css` → `styles/literary-album/{core,landing,pages}.css` (P9)
- ⏭ `index.css` ~2800 строк — следующий split

### Frontend — CSS-сироты (устарело)
- `index.css`: `.landing-page`, `.hero-orbs*`, `.quick-nav-*`
- `literary-album.css`: `.epic-verses-*`, `.literary-gallery-*`, `.seasonal-tip*`

### Frontend — дубли логики (снято в P3)
- ~~`Complaints` + `OfficialIssues` + admin `Issues` — три UI обращений~~ → `LiteraryIssueCard` + `IssuesWorkbench`
- ~~`Jobs` ≈ `Classifieds` — форма дублируется~~ → `ClassifiedAdForm`

### Backend — shim-файлы
- ✅ Все VK/utils re-export shims удалены (P0–P6)
- ✅ `vk_messages.py` удалён — канон: `vk/messages.py`

### Backend — «боги»
- ✅ `models/enums.py` → `models/enums/` (P5)
- ✅ `lib/api/types.ts` → `lib/api/types/` (P6)

### Прочее лишнее
- Черновые PR #20–#28 — устарели, закрыть
- `navigation.ts` — `QUICK_NAV_*` без CSS и без потребителей
- `portalCopyShared` — `PORTAL_COPY_LINKS`, `PORTAL_COPY_VK` покрыты Vitest
- ~~`Signup.tsx` — хардкод вместо `literaryCopy`~~ → `PAGE_SECTIONS.signup`

---

## 🔜 Куда двигаться (приоритет)

### P0 — быстрая чистка ✅ (2026-06-16)
1. ✅ Удалены мёртвые компоненты и VK shims без импортов
2. ✅ Webhook/admin/background_tasks → `services/vk/` напрямую
3. ✅ Общий `eventRegionFilters.ts` для афиши
4. ✅ Удалены utils-shims (`pagination_utils` → `app.utils`)
5. ✅ Удалены оставшиеся VK re-export shims (7 файлов)
6. ✅ Мёртвый CSS: quick-nav, hero-orbs, verses, seasonal-tip, gallery

### P1 — качество и тесты ✅ (2026-06-16)
1. ✅ Backend: `test_auth_api.py`, `test_classified_api_db.py`, `test_provider_booking_db.py`
2. ✅ Frontend: Vitest `useSiteInfo`, `useToday`, `portalCopyCross`
3. ✅ Cross-test: `test_portal_copy_cross.py` + `portalCopyCross.test.ts`
4. ⏭ Расширить `portal_copy.json` — EMPTY_STATES (опционально, P3)

### P2 — разбиение оставшихся god files ✅ (2026-06-16)
1. ✅ `provider_service.py` → package `provider/`
2. ✅ `issue_processor.py` → `issue/ingest.py` (+ gemini, dedup, residents)
3. ✅ `event_service.py` → package `event/`
4. ✅ `vk_messages.py` → `vk/messages.py`

### P3 — UX consolidation ✅ (2026-06-16)
1. ✅ `LiteraryIssueCard` + `IssuesWorkbench` — единый список (Complaints, Official, Admin, Cabinet)
2. ✅ `ClassifiedAdForm` + `useFormDraft` на Jobs; `LiteraryJobCard`
3. ✅ Admin `Issues` → dedicated `issues-workbench` shell (без shadcn/literary mix)

### P4 — VK Mini App ✅ foundation (2026-06-16)
1. ✅ `VK_APP_ID`, `VK_APP_SECRET`, CORS vk.com, CSP `frame-ancestors` для `/vk`
2. ✅ `POST /api/v1/vk/auth` — launch params → JWT
3. ✅ Shell `/vk/*` — табы: афиша, объявления, обращения, кабинет
4. ⏭ Прод: зарегистрировать App ID в VK, прописать секрет на VPS

### P2b — god files ✅ (2026-06-16)
1. ✅ `weather_service.py` → `weather/` (fetch, format, schemas)
2. ✅ `vk/commands.py` → `vk/commands/` (handlers, aliases)

### P9 — большой прогон ✅ (2026-06-16)
1. ✅ CSS split: `literary-album/` → core + landing + pages
2. ✅ `landing_hero` в `portal_copy.json` + cross-тесты
3. ✅ Backend: `test_feedback_visits_api`, `test_ai_api`, health redis ping
4. ✅ `buildIssueWorkbenchQuery`, `useIssuesWorkbench.test.ts` (@testing-library/react)
5. ✅ Vitest **58**

### P8 — тексты и admin API (без VK Mini App) ✅ (2026-06-16)
1. ✅ `EMPTY_STATES` → `shared/portal_copy.json` (frontend + backend sync)
2. ✅ `test_admin_api_db` — statistics, audit-logs, notifications (owner-only)
3. ✅ `issueWorkbenchTotalPages` helper + Vitest **57**

### P7 — тесты и утилиты (без VK Mini App) ✅ (2026-06-16)
1. ✅ Backend: `test_places_api_db`, `test_map_meta_api`, `test_weather_api`, `test_health_api`
2. ✅ Frontend: `formDraftStorage`, `mapTiles`, `siteUrl` — Vitest **55**
3. ✅ `useFormDraft` → `formDraftStorage` helpers (тестируемые без renderHook)

### P6 — инфра и чистка (без VK Mini App) ✅ (2026-06-16)
1. ✅ Redis rate limit: `redis` в `docker-compose.prod.yml`, `REDIS_URL`, slowapi storage
2. ✅ Исправлен `test_vk_unsubscribe_command` (mock → `commands.handlers`)
3. ✅ `lib/api/types.ts` → `lib/api/types/` (auth, issues, places, …)
4. ✅ Удалён мёртвый CSS: `landing-jobs-grid`, `literary-useful-grid--landing`, closing verse
5. ✅ Удалён shim `vk_messages.py`

### P5 — продукт (без VK Mini App) ✅
- ✅ Исправлен cross-test `portal_copy` (`welcome_body`)
- ✅ `models/enums.py` → package `models/enums/` (user, catalog, classified, issue, place, event)
- ✅ `Signup.tsx` → `PAGE_SECTIONS.signup`
- ✅ PWA: manifest shortcuts, SW shell cache v8, синхрон тайл-кэша, UX кнопки офлайн-карты
- ✅ Vitest **47** (цель 40+)
- ⏭ Redis rate limit (нужен redis в compose)
- ⏭ VK Pay (если монетизация)
- ⏭ VK Mini App — **не трогаем** (App ID, `/vk/*`)

---

## Метрики

| Метрика | Сейчас | Цель ROADMAP |
|---------|--------|--------------|
| Smoke | 26 OK | 26+ |
| pytest | ~175 | 120+ |
| Vitest | **58** | 40+ |
| God CSS | literary-album split ✅ | index.css |
| Мёртвые компоненты | 0 | 0 |
| VK shim files | 0 | 0 |

---

## Команды

```bash
# Деплой (пароль в .deploy.env)
BRANCH=main bash scripts/remote-deploy.sh

# Тесты
cd backend && pytest
cd frontend && npm run test && npm run build
```

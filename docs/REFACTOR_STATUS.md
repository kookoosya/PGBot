# Статус рефакторинга портала Пушкинские Горы

**Прод:** https://192-210-213-135.sslip.io  
**Деплой:** `bash scripts/remote-deploy.sh` (пароль в `.deploy.env` или `VPS_PASSWORD`)  
**Обновлено:** 2026-06-16

---

## Сводка

| Область | Готово | В работе / осталось |
|---------|--------|---------------------|
| Инфра / деплой | sslip.io, smoke 26, cron афиши, 2 workers | DNS .ru отложен |
| Backend домены | `issue/`, `place/`, `classified/`, `provider/`, `event/`, `weather/`, `vk/` | — |
| Backend тесты | ~99 pytest | auth, admin, providers, map, AI — без покрытия |
| Frontend API | split `lib/api/*` | `types.ts` ~630 строк |
| Frontend Map | split `pages/map/*` | — |
| Frontend UI | literary album, unified issue/ad components | — |
| Frontend тесты | Vitest 13 (eventUtils, literaryCopy) | компоненты, API hooks |
| Тексты | `shared/portal_copy.json` brand + issue hints | bulk UI copy только во frontend |
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

### Frontend — CSS-сироты (после удаления компонентов)
- `index.css`: `.landing-page`, `.hero-orbs*`, `.quick-nav-*`
- `literary-album.css`: `.epic-verses-*`, `.literary-gallery-*`, `.seasonal-tip*`

### Frontend — дубли логики (снято в P3)
- ~~`Complaints` + `OfficialIssues` + admin `Issues` — три UI обращений~~ → `LiteraryIssueCard` + `IssuesWorkbench`
- ~~`Jobs` ≈ `Classifieds` — форма дублируется~~ → `ClassifiedAdForm`

### Backend — shim-файлы (re-export, можно убрать после миграции импортов)
| Shim | Канонический путь | Импортёров |
|------|-------------------|------------|
| `vk_command_router.py` | `vk.command_router` | webhook |
| `vk_moderation_service.py` | `vk.moderation` | webhook, admin |
| `vk_flows.py`, `vk_flow_store.py` | `vk.flows`, `vk.flow_store` | webhook, tests |
| `vk_digest.py` | `vk.digest` | background_tasks |
| `ai_mode.py`, `vk_ai_mode_store.py` | `vk.ai_mode` | webhook, tests |
| `vk_bot.py`, `vk_subscription.py`, `vk_voice.py`, `vk_ai_history.py` | `vk/*` | **0 — удалить** |
| `pagination_utils`, `notify_utils`, `datetime_utils`, `service_errors` | `app/utils/*` | ~15 |

### Backend — «боги» (ещё не разбиты)
| Файл | Строк | Рекомендация |
|------|------:|--------------|
| `models/enums.py` | ~286 | split по доменам |

### Прочее лишнее
- Черновые PR #20–#28 — устарели, закрыть
- `navigation.ts` — `QUICK_NAV_*` без CSS и без потребителей
- `portalCopyShared` — `PORTAL_COPY_LINKS`, `PORTAL_COPY_VK`, `ISSUE_STATUS_EMOJI` не используются во frontend
- `Signup.tsx` — хардкод вместо `literaryCopy`

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

### P5 — продукт
- PWA / офлайн-карта
- Redis rate limit (PR #20)
- VK Pay (если монетизация)

---

## Метрики

| Метрика | Сейчас | Цель ROADMAP |
|---------|--------|--------------|
| Smoke | 26 OK | 26+ |
| pytest | ~133 | 120+ |
| Vitest | 26 | 40+ |
| God files ≥400 строк | 0 | 0 |
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

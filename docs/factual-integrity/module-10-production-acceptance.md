# Module 10 — production acceptance

**Baseline SHA:** `a9b04ea7df1086cfa9a23b40a54005b707005fa3`  
**Production SHA (at acceptance):** `a9b04ea`  
**Date:** 2026-07-03

## Git

| Check | Result |
|-------|--------|
| Branch | `main` |
| Worktrees | 1 |
| HEAD == origin/main | `a9b04ea` |
| Temp scripts | removed (Module 9 cleanup) |
| Untracked | `frontend/docs/` (verification artifact, not committed) |

## Tests

| Suite | Result | Notes |
|-------|--------|-------|
| Backend `pytest -m "not postgres"` | **341 passed**, 1 skipped | local |
| PostgreSQL `pytest -m postgres` | **85 skipped** | local DB unavailable |
| Frontend `npm ci && npm test && build` | **Cannot run locally** | `EPERM` on `node_modules` unlink |
| CI [#430](https://github.com/kookoosya/PGBot/actions/runs/28673942197) | **success** | backend, postgres, frontend, smoke-prod |
| Production smoke (deploy) | **33 OK, 0 FAIL** | Module 9 deploy |

## Production `/health`

```json
{"git_commit":"a9b04ea","status":"ok"}
```

## SPA routes (HTTP 200)

Главная, Карта, Афиша, Объявления, Услуги, Обращения — все **200**.

## Navigation (10 cycles)

`Главная → Карта → Афиша → Объявления → Услуги → Главная` × 10 — все маршруты **200**.  
2 transient `fetch` errors в browser evaluate (сеть), не воспроизведены при повторной загрузке.

## Map counts (production API + browser)

| Metric | Value |
|--------|-------|
| catalog (`scope=VILLAGE`) | **45** |
| sum(`by_category`) | **45** |
| hidden categories (UI) | **16** (top-8 = 29) |
| desktop visible / list / clusters | **45 / 45 / 45** |
| mobile visible / list / clusters | **29 / 29 / 29** |

### Category totals (`/places/map/stats?scope=VILLAGE`)

| Category | Count |
|----------|-------|
| supermarket | 5 |
| pharmacy | 3 |
| auto | 5 |
| car_wash | 2 |
| auto_parts | 3 |
| hospital | 1 |
| vet | 1 |
| gas | 1 |
| tyre | 1 |
| school | 2 |

### Map UI (Module 9)

- Filter loading: **«Обновляем список…»**, `visible=null`, markers=0
- Супермаркеты после ответа: **5** = list IDs = clusters
- Старое число под новым фильтром: **не воспроизведено**
- Emoji категорий: **сохранены** (🔧 🏪 💊 🧽 …)
- Leaflet Ukraine flag: **отсутствует** (стандартная attribution ссылка на leafletjs.com — ожидаемо)

## Modules 1–5 (production API)

| Requirement | Result |
|-------------|--------|
| Village hospital count | **1** in `by_category` |
| District FAPs excluded from village stats | **confirmed** (`hospital` district search = 4, village = 1) |
| 3 pharmacies | **3** |
| Vet separate category | **1** |
| 5 auto services | **5** in village stats |
| 2 car wash | **2** |
| 3 auto parts | **3** |
| 1 AZS | **1** |
| Work.Taxi not published | **0** search hits |
| РАЙПО not as map point | search finds shop names, **not** Work.Taxi |
| МФЦ | **1** search hit |
| «Съешка» | **1** search hit |
| «Пушкиногорье» (турбаза) | **4** hits (lodging cluster) |
| «Сургутнефтегаз» | **1** hit |
| Шиномонтаж Аэродромная | **1** hit; place id **327** in cluster set |

### Cannot verify on production without owner field in API response

- `OWNER_CONFIRMED` status on place 327 (inventory documents it; public API may not expose field)
- Exact phone `+7 (906) 221-03-54` on live place card (timeout on detail fetch during audit)
- КДЦ as map point (search **0**; may exist only as event source)
- Столовая на Турбазе as separate named point
- Single school at Лермонтова 13 vs `school: 2` in stats (both may be valid village schools)

## Афиша (Module 6)

| Check | Result |
|-------|--------|
| `EVENT_SYNC_INTERVAL_HOURS` default | **4** (config + tests) |
| Scheduler interval | **14400 s** (tests) |
| Events page | **200** |
| Events unique IDs | **50/50** (no duplicates in sample) |
| Actual 4h re-sync on production | **Cannot be verified** (requires 4h wait) |
| Map sync interval | **unchanged** (6h in UI) |

## Performance (Module 8)

| Check | Result |
|-------|--------|
| `main` stable across routes | **covered by** `PublicLayout.navigation.test.tsx` |
| Production main remount | **Cannot be verified** without React DevTools |
| Fade restart / blank screen | **0** in navigation test suite; brief album loader on first paint only |
| Map listeners off `/map` | **Cannot be verified** in this audit |

## Console / network

- Fatal console errors during browser audit: **0 observed**
- Unexpected failed requests: **2 transient** fetch in stress script only

## Defects found

**None blocking.** No code changes in Module 10.

## Changes in this module

- `docs/factual-integrity/module-10-production-acceptance.md` (this file)
- `docs/factual-integrity/module-09-map-result-atomicity.md` (post-deploy section, carried from prior session)

## CI / Deploy (Module 10)

Will be recorded after docs commit push.

## Stage status

**CURRENT PRODUCTION STAGE ACCEPTED** — pending final docs commit SHA on `/health` if redeployed.

## Next module

**NOT STARTED.**

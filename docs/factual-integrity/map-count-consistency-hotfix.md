# Map count consistency hotfix

**Baseline SHA:** `e2f6602c42fbc1333cee1d90bd5ff0aa5ef47ef0`  
**Audit date:** 2026-07-03

## Fail-before (production, ae66923/e2f6602 era)

| Счётчик | Значение | Что реально считает |
|---------|----------|---------------------|
| DB village active (`total_places`) | 45 | Все active scope=VILLAGE |
| sum(`by_category`) | 45 | Совпадает с catalog total ✓ |
| Visible top-8 sum | 34 | Только 8 категорий в ribbon |
| Hidden categories | 11 | 16 категорий, 8 скрыты без пояснения |
| `reference_places` (до fix) | 59 | Все reference globally, не только VILLAGE |
| Ribbon label | «45 мест на карте» | **Неверно** — это catalog, не viewport |
| List tab / `places.length` | bbox subset | Только items в viewport, не `response.total` |
| Visible cluster icons | < M | Leaflet clustering — нормально |

**Backend count defect:** не обнаружен для `total_places` vs `sum(by_category)`.  
**UI semantics defect:** подтверждён — смешение catalog total, скрытых категорий и viewport count.

## Root cause

1. **Mislabeling:** `stats.total_places` показывался как «N мест на карте», хотя это весь справочник VILLAGE.
2. **Hidden categories:** `.slice(0, 8)` без subtotal для остальных 11 организаций.
3. **Viewport vs catalog:** список и вкладка использовали `places.length` вместо `response.total`.
4. **reference_places:** считался без scope filter (59 vs 45 village).
5. **Clusters:** визуально меньше иконок — ожидаемое поведение, не баг.

## Fix

### Backend (`stats.py`)
- `catalog_places` — active VILLAGE catalog total
- `mappable_places` — active VILLAGE с координатами в settlement bbox
- `reference_places` — scoped to requested scope
- `total_places` сохранён для совместимости (= catalog)

### Frontend
- **MapStatsRibbon:** «Всего в справочнике», опционально «С координатами», «В текущей области»
- **Остальные категории: N** под top-8
- **useMapPage:** `currentAreaCount` из `response.total`, stale-safe (Module 7)
- **Map / PlacesList / mobile tab:** единый `currentAreaCount`
- **MapMoreCategories:** subtotal и counts per category

## Tests

- `backend/tests/test_map_count_consistency.py`
- `frontend/src/pages/map/mapCountConsistency.test.tsx`
- Extended `useMapPage.places.test.ts`

## Cannot be verified (pre-deploy)

- Live cluster DOM count vs M (clustering library)

## Post-deploy verification (2026-07-03)

**Final SHA:** `e197a177528989a5b85619028a21125ba9613ae2`  
**CI:** run [#429](https://github.com/kookoosya/PGBot/actions/runs/28670293893) — success  
**Deploy:** attempt 29/50 via `agent-deploy.mjs` — smoke 33 OK, 0 FAIL  
**`/health` git_commit:** `e197a17`

| Счётчик | Production |
|---------|------------|
| catalog (Всего в справочнике) | 45 |
| mappable | 45 (равно catalog — строка «С координатами» скрыта) |
| sum(by_category) | 45 |
| top-8 sum | 29 |
| hidden categories | 16 |
| current area (desktop full viewport) | 45 |
| current area (mobile initial) | 30 |
| list tab count | совпадает с current area |
| cluster org sum (desktop) | 45 |
| cluster org sum (mobile) | 29 (viewport subset) |

**Browser checks:** 10+ zoom/pan cycles; фильтр «Супермаркет» → M=5 после ответа API; N=45 стабилен при zoom; нет «N мест на карте»; «Остальные категории: 16» видна.

**Screenshots:** `docs/screenshots/map-count-hotfix/` (не коммитятся)

### Cannot be verified

- List row DOM count vs M (селекторы списка в headless не совпали с разметкой)
- Transient filter label/count mismatch during loading (~2s после смены категории — старый total + новый filter label; после ответа API сходится)

## Module 9

**NOT STARTED.**

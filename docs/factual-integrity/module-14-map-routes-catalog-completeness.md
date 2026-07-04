# Module 14 — Map / Routes / Catalog Completeness

**Status:** COMPLETE (pending deploy verification)  
**Baseline:** `7d4eda4`  
**Branch:** `main`

## Problem

Users reported the map/catalog felt incomplete: too few route cards, tire service looked promoted in the bottom route block, and category coverage (food, hotels, pharmacies) should be re-checked without inventing data.

## Summary

| Metric | Before (prod) | After (code) |
|--------|---------------|--------------|
| Village catalog (`scope=VILLAGE`) | 45 | 45 (unchanged) |
| Recommended/bottom routes | 4 (incl. `auto-aerodromnaya`) | 11 (no tyre route) |
| Verified phones in inventory | 24 | 24 (unchanged) |
| Tyre on map/catalog | yes | yes |
| Tyre in route cards | yes (`auto-aerodromnaya`) | **no** |

## Route changes

**Removed from routes (not from catalog):**

| Route ID | Action | Reason |
|----------|--------|--------|
| `auto-aerodromnaya` | REMOVE_FROM_ROUTES_ONLY | User request: tyre stays on map but must not appear promoted |

**Restored / added verified routes** (stops use inventory coords + sources):

| Route ID | Title | Category focus |
|----------|-------|----------------|
| `pushkin-classic` | Классический Пушкин | tourist |
| `pushkin-estate-day` | Михайловское: день на усадьбе | tourist |
| `pilgrim` | Паломнический | tourist |
| `village-evening` | Вечерний посёлок | food |
| `village-services` | Посёлок: бытовой маршрут | services |
| `from-bus` | Приехал на автобусе | transport/tourist |
| `village-food` | Где поесть в посёлке | cafes/restaurants |
| `village-hotels` | Где остановиться | hotels |
| `pharmacy-health` | Аптеки и медицина | pharmacy/hospital |
| `public-services` | Полезное в посёлке | government/post/bank/shops |
| `culture-kdc` | Культура и КДЦ | culture |

## Audit table (village_active = 45)

Action legend: `KEEP_VERIFIED`, `ADD_VERIFIED`, `UPDATE_VERIFIED`, `REMOVE_FROM_ROUTES_ONLY`, `MARK_UNVERIFIED`, `REJECT_NOT_VERIFIED`.

### Cafes / restaurants / столовые

| Name | Category | Address | Phone | Source | Inventory | Production | Action |
|------|----------|---------|-------|--------|-----------|------------|--------|
| Кафе «Пушкинъ» | cafe | пл. Ленина, 3 | — | yandex.ru/maps | active | API | KEEP_VERIFIED |
| Святогоръ | cafe | ул. Ленина, 2 | — | 2gis.ru | active | API | KEEP_VERIFIED |
| Сиежка | cafe | ул. Пушкинская, 69 | — | yandex.ru/maps | active | API | KEEP_VERIFIED |
| Пушкин-Парк | restaurant | ул. Ленина, 42А | — | 2gis.ru | active | API | KEEP_VERIFIED; route stop name fixed from erroneous «Быков-угол» |
| Пушкиногорье, столовая | restaurant | ул. Турбаза | — | yandex.ru | active | API | KEEP_VERIFIED |
| Берёзка | cafe | с. Михайловское | — | yandex.ru | nearby | map | KEEP_VERIFIED (NEARBY_ATTRACTION) |

### Hotels / guest houses

| Name | Category | Address | Phone | Source | Inventory | Production | Action |
|------|----------|---------|-------|--------|-----------|------------|--------|
| Дружба | hotel | ул. Ленина, 8 | UNVERIFIED | yandex.ru/maps | active | API | KEEP_VERIFIED |
| Усадьба Тригорская | hotel | ул. Тригорская, 1 | UNVERIFIED | 2gis.ru | active | API | KEEP_VERIFIED |
| Дом Классика | hotel | ул. Пушкинская, 47 | UNVERIFIED | yandex.ru/maps | active | API | KEEP_VERIFIED |
| Пушкиногорье | hotel | микрорайон Турбаза | 8-800-250-17-99 | pgtur.ru | active | API | KEEP_VERIFIED |
| Гостиница «Пушкиногорская» | hotel | ул. Новоржевская, 18 | — | — | rejected | absent | REJECT_NOT_VERIFIED — Cannot be verified |

### Pharmacies / medical

| Name | Category | Address | Phone | Source | Inventory | Production | Action |
|------|----------|---------|-------|--------|-----------|------------|--------|
| Аптека-А | pharmacy | ул. Ленина, 20А | +7 (81146) 2-15-15 | 2gis.ru | active | API | KEEP_VERIFIED |
| Аптека-А | pharmacy | ул. Новоржевская, 25 | +7 (81146) 2-15-15 | yandex.ru/maps | active | API | KEEP_VERIFIED |
| Фарм-М | pharmacy | ул. Ленина, 42 | +7 (960) 222-67-76 | yandex.ru/maps | active | API | KEEP_VERIFIED |
| Пушкиногорская межрайонная больница | hospital | ул. Ленина, 41 | +7 (81146) 2-27-06 | pushgori-crb.ru | active | API | KEEP_VERIFIED |
| ФАП д.Блажи | hospital | д. Блажи | — | yandex.ru | district | absent village | KEEP_VERIFIED (MUNICIPAL_DISTRICT) |
| ФАП д.Крылово | hospital | д. Крылово | — | yandex.ru | district | absent village | KEEP_VERIFIED (MUNICIPAL_DISTRICT) |

### Tire / auto services

| Name | Category | Address | Phone | Source | Inventory | Production | Action |
|------|----------|---------|-------|--------|-----------|------------|--------|
| Шиномонтаж | tyre | ул. Аэродромная, 23 | +7 (906) 221-03-54 (OWNER_CONFIRMED) | owner:project / 2gis.ru | active | API | KEEP_VERIFIED; **REMOVE_FROM_ROUTES_ONLY** |

### Tourist / culture / public services

| Name | Category | Address | Phone | Source | Action |
|------|----------|---------|-------|--------|--------|
| ГМЗ «Михайловское» | culture | бульвар им. С. С. Гейченко, 1 | +7 (81146) 2-23-28 | pushkinland.ru | KEEP_VERIFIED |
| Святогорский монастырь | culture | ул. Пушкинская, 1 | +7 (81146) 2-16-44 | svyatogorskiy-monastery.ru | KEEP_VERIFIED |
| МБУК КДЦ | culture | ул. Садовая, 1 | +7 (81146) 2-13-70 | kdc-pushgory.ru | KEEP_VERIFIED |
| НКЦ «Пушкинские Горы» | culture | ул. Ленина, 2 | — | pushkinland.ru | KEEP_VERIFIED |
| МФЦ «Мои документы» | government | ул. Ленина, 6 | +7 (8112) 29-92-98 | mfc.pskov.ru | KEEP_VERIFIED |
| Администрация ПМО | government | ул. Ленина, 6 | +7 (81146) 2-10-01 | admpushgory.ru | KEEP_VERIFIED |
| Почта России | post | ул. Ленина, 22 | — | yandex.ru/maps | KEEP_VERIFIED |
| Сбербанк (банкомат) | bank | ул. Ленина, 40 | — | sberbank.ru | KEEP_VERIFIED |
| Автовокзал Пушкинские Горы | transport | ул. Новоржевская, 30 | — | openstreetmap.org | KEEP_VERIFIED |

### Transport / taxi

| Name | Category | Action | Note |
|------|----------|--------|------|
| Work.Taxi | taxi | REJECT_NOT_VERIFIED | No verified address/coords — not seeded |

## Cannot be verified (no change)

- **Гостиница «Пушкиногорская»** (ул. Новоржевская, 18) — no Yandex/2GIS org card, no coords.
- **Unverified cafe/hotel phones** — left null / `phone_status: UNVERIFIED`; no invented numbers.
- **Historical 11-route set (pre-`e2799f5`)** — several stops used unverified coords (e.g. Mikhailovskoe village center); not blindly restored.

## Tests added/updated

- `backend/tests/test_module14_map_routes_catalog.py` — route count, tyre exclusion, search, phones, duplicates
- `test_map_reference_integrity_stage01.py` — tyre absent from routes, present in seed
- `test_map_reference_integrity_stage02.py` — route count ≥ 8, tyre absent

## Deploy

Required: yes (routes API + stats `route_count` change).

Post-deploy checks: `/health`, smoke, catalog=45, routes=11, search cafe/hotel/pharmacy/КДЦ, tyre on map, tyre absent from `/api/v1/places/routes`.

# Module 16 — Public «Номера» Tab Completeness

**Status:** COMPLETE  
**Baseline:** `4f8bb5e`  
**Final:** `c37cc2d`  
**Branch:** `main`

## User complaint

Раздел «Номера» на карте показывал только 5 экстренных номеров + 3 статических контакта (музей, монастырь, больница). Verified телефоны из справочника (20 шт. в API) не отображались. Вкладка «Такси» была пустой без объяснения.

## Fail-before (production @ `4f8bb5e`)

| Metric | Value |
|--------|------:|
| `/health` | `4f8bb5e` |
| Visible cards in «Номера» UI | **8** (5 emergency + 3 static) |
| Verified phones in API | **20** |
| Taxi tab | **empty** (null render, no message) |
| Defect | **CONFIRMED** |

## Root cause

`HotlinesPanel` рендерил только hardcoded массив `VILLAGE_HOTLINES` из `hotlines.ts` и **не** использовал public places API. `TaxiPanel` при `taxi.length === 0` возвращал `null` без empty-state. `TAXI_SEED` пуст — verified taxi phones отсутствуют.

## Fix

1. `verifiedPhoneContacts.ts` — mapper: API places с `phone` → группы по категориям, dedupe по номеру.
2. `useVerifiedPhoneContacts.ts` — загрузка `/api/v1/places?scope=VILLAGE&page_size=500`.
3. `HotlinesPanel` — emergency сверху + grouped verified contacts из API.
4. `TaxiPanel` — empty-state: «Проверенные номера такси пока не добавлены».
5. `MapServicesTabs` — динамический счётчик номеров вместо hardcoded «14 номеров».

Backend/inventory **не менялись**.

## Contact contract

- Emergency: 112, 101, 102, 103, 104 (static)
- Verified place phones from API only
- Groups: медицина, госуслуги, такси/транспорт, еда/отели, авто, культура, прочее
- Hidden: null/unverified phones (API contract unchanged)

## Taxi verification

| Record | Result |
|--------|--------|
| Work.Taxi | **REJECT_UNVERIFIED** — no verified address/phone (inventory) |
| TAXI_SEED | **empty** |
| UI | **SHOW_TAXI_EMPTY_STATE** |

## Cannot be verified

- Verified taxi phone numbers — none in inventory/API
- Cafe/restaurant/hotel phones — remain null in inventory (not added)

## Tests

- `verifiedPhoneContacts.test.ts`
- `HotlinesPanel.test.tsx`
- `TaxiPanel.test.tsx`
- Updated `mapFactualIntegrity.test.ts`

## Changed files

- `frontend/src/pages/map/verifiedPhoneContacts.ts` (new)
- `frontend/src/pages/map/useVerifiedPhoneContacts.ts` (new)
- `frontend/src/pages/map/HotlinesPanel.tsx`
- `frontend/src/pages/map/TaxiPanel.tsx`
- `frontend/src/pages/map/MapServicesTabs.tsx`
- `frontend/src/pages/map/hotlines.ts`
- `frontend/src/styles/portal/map.css`
- Tests + this audit doc

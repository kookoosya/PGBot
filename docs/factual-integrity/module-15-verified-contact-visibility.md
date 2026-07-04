# Module 15 — Verified Contact Visibility

**Status:** COMPLETE  
**Baseline:** `50d94cd`  
**Branch:** `main`

## Production baseline (before Module 15 code)

| Check | Result |
|-------|--------|
| `/health` git_commit | `a451590` (expected: docs-only `50d94cd` not deployed yet) |
| Village catalog | **45** |
| Routes | **11** (tyre absent) |
| API places with `phone` | **20** |
| Inventory verified phones (`_public_phone`) | **20** |

Production API matched seed contract: **20/20** verified phones visible in list endpoint.

## Contact totals

| Metric | Count |
|--------|------:|
| Village places (`scope=VILLAGE`) | 45 |
| Inventory `phone` not null | 24 |
| Inventory `phone_status` verified (not UNVERIFIED) | 20 |
| Seed / public API phones | 20 |
| UI list/detail when API returns phone | 20 |
| Intentionally hidden toll-free (`phone_status=UNVERIFIED`) | 4 |
| No phone in inventory (cannot publish) | 21 |

## Hypothesis results

| ID | Hypothesis | Result |
|----|------------|--------|
| A | Inventory phone, seed does not transfer | **REJECTED** — 20/20 verified phones seed to DB |
| B | DB has phone, list API omits | **REJECTED** — list returns same `phone` field |
| C | Detail has phone, list does not | **REJECTED** — same `PlaceResponse` serializer |
| D | API has phone, frontend hides | **REJECTED** — `PlacesList` + `PlaceDetailPanel` render `phone` |
| E | Verified status hidden by mistake | **REJECTED** — all `phone_status != UNVERIFIED` published |
| F | Search loses phone | **REJECTED** — search uses same list serializer |
| G | Mobile layout hides contacts | **REJECTED** — no CSS rule hides `.org-list-card` phone |
| H | Verified social links not shown | **REJECTED** — all `social_url` are null in inventory |
| I | Tyre only in detail | **REJECTED** — id 326 phone in list + detail on production |
| J | Pharmacy/MFC lost via alias/serializer | **REJECTED** — verified pharmacy/MFC phones present in API |

**Root cause of user complaint:** Per contract (`_public_phone`), only **20** of **24** non-null inventory phones are verified for publication. The other **4** are chain toll-free numbers (`8-800-*`) with `phone_status: UNVERIFIED`. An additional **21** village places have no verified phone in inventory (cafes, hotels, vet, car wash, etc.). This is **not a seed/API/UI regression** — it is intentional factual quarantine from Module 1–2.

## Verified phones (20) — all `KEEP_VERIFIED_VISIBLE`

| stable_key | name | category | phone | phone_status |
|------------|------|----------|-------|--------------|
| shinomontazh-aerodromnaya-23 | Шиномонтаж | tyre | +7 (906) 221-03-54 | OWNER_CONFIRMED |
| apteka-a-novorzhevskaya-25 | Аптека-А | pharmacy | +7 (8112) 60-77-11 | YANDEX_ACTIVE |
| farm-m-lenina-42 | Фарм-М | pharmacy | +7 (960) 222-67-76 | YANDEX_ACTIVE |
| hospital-pushkinogorsky-filial | Пушкиногорская межрайонная больница | hospital | +7 (81146) 2-27-06 | OFFICIAL_PRIMARY |
| mfc-lenina-6 | МФЦ «Мои документы» | government | +7 (8112) 29-92-98 | YANDEX_ACTIVE |
| administratsiya-lenina-6 | Администрация ПМО | government | +7 (81146) 2-13-37 | OFFICIAL_PRIMARY |
| kdc-sadovaya-1 | МБУК КДЦ | culture | +7 (81146) 2-33-03 | YANDEX_ACTIVE |
| museum-mikhailovskoe-nkc | ГМЗ «Михайловское» | culture | +7 (81146) 2-23-21 | OFFICIAL_PRIMARY |
| monastery-svyatogorsky | Святогорский монастырь | culture | +7 (81146) 2-33-89 | OFFICIAL_PRIMARY |
| nkc-pushkinskie-gory | НКЦ «Пушкинские Горы» | culture | +7 (81146) 2-23-21 | OFFICIAL_PRIMARY |
| school-1-lenina-30 | Средняя школа им. А.С. Пушкина | school | +7 (81146) 2-13-30 | YANDEX_ACTIVE |
| turbaza-pushkinogorye | Пушкиногорье | hotel | 8-800-250-17-99 | YANDEX_ACTIVE |
| azs-pskovnefteprodukt-novorzhevskaya-31 | АЗС Псковнефтепродукт | gas | +7 (81146) 2-12-07 | YANDEX_ACTIVE |
| serviseklass-stroiteley-13 | Serviseklass | auto | +7 (921) 607-74-60 | YANDEX_ACTIVE |
| avtoservis-pushkinskaya-42b | Автосервис | auto | +7 (911) 350-12-42 | YANDEX_ACTIVE |
| avtoservis-aerodromnaya-4b | Avtoservis | auto | +7 (953) 231-68-15 | YANDEX_ACTIVE |
| fixcar-lenina-29 | Fixcar | auto | +7 (921) 607-96-67 | YANDEX_ACTIVE |
| avtozapchasti-lermontova-10 | Автозапчасти | auto_parts | +7 (911) 886-76-00 | YANDEX_ACTIVE |
| raypo-trigorskaya-3 | Потребительский союз | supermarket | +7 (81146) 2-31-45 | YANDEX_ACTIVE |
| sberbank-atm-lenina-40 | Сбербанк (банкомат) | bank | 900 | OFFICIAL_PRIMARY |

## Intentionally without public phone

| Group | stable_keys | Reason |
|-------|-------------|--------|
| Toll-free hidden | pyaterochka-lenina-20a, pyaterochka-pushkinskaya-11, magnit-lenina-42, magnit-novorzhevskaya-25 | `HIDE_UNVERIFIED_BY_CONTRACT` — `8-800-*`, `phone_status: UNVERIFIED` |
| Pharmacy without verified phone | apteka-a-lenina-20a | 2GIS card exists; phone not confirmed — `INSUFFICIENT_EVIDENCE` |
| Vet / art school / cafes / hotels / car wash / transport | vet-sbbzh-stroiteley-3, art-school-geychenko-pushkinskaya-3, kafe-pushkin-lenina-3, svyatogor-cafe-lenina-2, sieszka-pushkinskaya-69, pushkin-park-lenina-42a, stolovaya-pushkinogorye-turbaza, druzhba-hotel-lenina-8, usadba-trigorskaya-hotel, dom-klassika-pushkinskaya-47, avtomoyka-*, car-wash-zvyozdnaya, avtovokzal-novorzhevskaya-30, … | `phone_status: UNVERIFIED` or `phone: null` — **Cannot be verified** without primary source |

Full per-place matrix: `stage-02-place-inventory.json` (45 village rows).

## Changes in Module 15

No production behavior change. Added:

- `backend/tests/test_module15_verified_contact_visibility.py` — contract/regression tests
- `frontend/src/pages/map/PlacesList.contact.test.tsx` — list card phone display
- This audit document

## Cannot be verified (no new phones added)

- Per-branch phones for cafes, restaurants, hotels (except turbaza toll-free), vet, art school, car washes, автовокзал
- Аптека-А ул. Ленина 20А — 2GIS supports phone field but value not captured/confirmed
- Any additional numbers from map aggregators without `phone_status` upgrade

## Tests

- Module 15 backend tests (inventory counts, seed sync, list/detail contract, Module 12–14 regressions)
- Frontend `PlacesList.contact.test.tsx`

## Deploy note

Deploy required so `/health` reflects Module 15 commit SHA (includes tests + audit; no API behavior change).

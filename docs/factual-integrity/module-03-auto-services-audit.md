# Module 3 — Auto Services Factual Integrity Audit

**Baseline:** `0d14b0ebb9c29b3df8b659b5e956737d6624e6c7`  
**Audit completed:** 2026-07-03T07:15:00Z (UTC)  
**Scope:** рп. Пушкинские Горы (`scope = VILLAGE` in main inventory)  
**Primary sources:** Yandex Maps (org cards opened individually)  
**2GIS:** automated access blocked (captcha on firm URLs and search). Existing tyre firm `70000001075370090` retained from prior verified inventory.

## OSINT passes

| Pass | Result |
|------|--------|
| Pass 1 | 18 Yandex queries + visual street checks; 10 new unique village auto orgs |
| Pass 2 | Same query set + extra queries (Иванов/Авторемонт/автоэлектроника/универсальная мастерская); **0 new unique orgs** |

Raw logs: `module-03-osint-raw.json`, `module-03-org-details.json`, `module-03-extra-search.json`.

## Yandex search log (all queries)

| # | Query | Checked | Cards reviewed | New unique | Notes |
|---|-------|---------|----------------|------------|-------|
| 1 | автосервис Пушкинские Горы | 2026-07-03 | 8 | 5 auto | Serviseklass, Автосервис 42Б, Avtoservis 4Б, Fixcar, Shinomontazh |
| 2 | СТО Пушкинские Горы | 2026-07-03 | 8 | 0 | Same core set |
| 3 | ремонт автомобилей Пушкинские Горы | 2026-07-03 | 8 | 0 | Same core set |
| 4 | ремонт авто Пушкинские Горы | 2026-07-03 | 8 | 0 | Same core set |
| 5 | диагностика автомобилей Пушкинские Горы | 2026-07-03 | 6 | 0 | Same core set |
| 6 | автоэлектрик Пушкинские Горы | 2026-07-03 | 6 | 0 | No standalone village org card |
| 7 | кузовной ремонт Пушкинские Горы | 2026-07-03 | 6 | 0 | Covered by existing autoservices |
| 8 | техническое обслуживание автомобилей Пушкинские Горы | 2026-07-03 | 6 | 0 | Same core set |
| 9 | замена масла Пушкинские Горы | 2026-07-03 | 6 | 0 | Same core set |
| 10 | шиномонтаж Пушкинские Горы | 2026-07-03 | 4 | 0 | Shinomontazh → KEEP_EXISTING |
| 11 | ремонт шин Пушкинские Горы | 2026-07-03 | 4 | 0 | Same |
| 12 | балансировка колёс Пушкинские Горы | 2026-07-03 | 4 | 0 | Same |
| 13 | автомойка Пушкинские Горы | 2026-07-03 | 3 | 2 car_wash | Автомойка (village card), Car wash Zvyozdnaya |
| 14 | мойка автомобилей Пушкинские Горы | 2026-07-03 | 3 | 0 | Same |
| 15 | автозапчасти Пушкинские Горы | 2026-07-03 | 3 | 3 auto_parts | Lermontova 10, 14А, Pushkinskaya 42А |
| 16 | магазин автозапчастей Пушкинские Горы | 2026-07-03 | 3 | 0 | Same |
| 17 | автомобильные масла Пушкинские Горы | 2026-07-03 | 3 | 0 | Same |
| 18 | эвакуатор Пушкинские Горы | 2026-07-03 | 0 | 0 | Empty results |
| 19 | Иванов Новоржевская 47 | 2026-07-03 | 5 | 1 auto | Автосервис Novorzhevskaya 47 |
| 20 | Авторемонт Ленина | 2026-07-03 | 5 | 0 | Fixcar Lenina 29 is separate confirmed org |
| 21 | +7 931 901-56-10 | 2026-07-03 | 8 | 0 | Phone not linked to auto service |
| 22 | автоэлектроника Пушкинские Горы | 2026-07-03 | 1 | 0 | Only Serviseklass overlap |
| 23 | универсальная мастерская Пушкинские Горы | 2026-07-03 | 1 | 0 | Search hit resolves to Sochi — see below |

## 2GIS search log

| Query set | Checked | Result |
|-----------|---------|--------|
| Same 18 queries as Yandex | 2026-07-03 | **Blocked** — captcha on all automated firm/search requests from audit IP |
| firm/70000001075370090 (tyre) | 2026-07-03 | Captcha — retain prior OWNER+2GIS inventory entry |

**Cannot be verified** via fresh 2GIS scrape in this audit run. Tyre shop 2GIS firm ID preserved from Module 2 baseline.

## Decision summary

| Decision | Count | stable_keys |
|----------|-------|-------------|
| ADD_ACTIVE | 10 | serviseklass-stroiteley-13, avtoservis-pushkinskaya-42b, avtoservis-aerodromnaya-4b, fixcar-lenina-29, avtoservis-novorzhevskaya-47, avtomoyka-pushkinskaya-42b, car-wash-zvyozdnaya, avtozapchasti-lermontova-10, zapchasti-lermontova-14a, avtozapchasti-pushkinskaya-42a |
| KEEP_EXISTING | 2 | shinomontazh-aerodromnaya-23 (enriched Yandex org id), azs-pskovnefteprodukt-novorzhevskaya-31 (Module 5 conflict — not resolved) |
| INSUFFICIENT_EVIDENCE | 1 | avtoremont-lenina |
| DUPLICATE_CONFIRMED | 0 | — |
| OUTSIDE_SCOPE | 1 | universalnaya_masterskaya Yandex id 144982715626 → Sochi, not village |
| CLOSED_CONFIRMED | 0 | — |

---

## Candidate tables

### shinomontazh-aerodromnaya-23 — KEEP_EXISTING

| Поле | Значение |
|------|----------|
| stable_key | shinomontazh-aerodromnaya-23 |
| public_name | Шиномонтаж |
| category | tyre |
| scope | VILLAGE |
| address | ул. Аэродромная, 23 |
| latitude | 57.017306 |
| longitude | 28.933486 |
| phone | +7 (906) 221-03-54 |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/shinomontazh/1703652438/ |
| Yandex ID | 1703652438 |
| 2GIS URL | https://2gis.ru/firm/70000001075370090 |
| 2GIS firm ID | 70000001075370090 |
| OSM | — |
| official/VK | pushkinskie-gory.xyz (Yandex card) |
| active status | ACTIVE |
| conflicts | none |
| decision | KEEP_EXISTING |

### serviseklass-stroiteley-13 — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | serviseklass-stroiteley-13 |
| public_name | Serviseklass |
| category | auto |
| scope | VILLAGE |
| address | ул. Строителей, 13 |
| latitude | 57.0338 |
| longitude | 28.9312 |
| phone | +7 (921) 607-74-60 |
| opening_hours | круглосуточно |
| Yandex URL | https://yandex.ru/maps/org/serviseklass/100030866827/ |
| Yandex ID | 100030866827 |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | none |
| decision | ADD_ACTIVE |

### avtoservis-pushkinskaya-42b — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | avtoservis-pushkinskaya-42b |
| public_name | Автосервис |
| category | auto |
| scope | VILLAGE |
| address | ул. Пушкинская, 42Б |
| latitude | 57.02157 |
| longitude | 28.9024 |
| phone | +7 (911) 350-12-42 |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/avtoservis/144919874621/ |
| Yandex ID | 144919874621 |
| 2GIS URL | Cannot be verified |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | Also lists car wash + tyre features (not duplicated) |
| decision | ADD_ACTIVE |

### avtoservis-aerodromnaya-4b — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | avtoservis-aerodromnaya-4b |
| public_name | Avtoservis |
| category | auto |
| scope | VILLAGE |
| address | ул. Аэродромная, 4Б |
| latitude | 57.019232 |
| longitude | 28.932166 |
| phone | +7 (953) 231-68-15 |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/avtoservis/69989070803/ |
| Yandex ID | 69989070803 |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | Also lists auto parts feature |
| decision | ADD_ACTIVE |

### fixcar-lenina-29 — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | fixcar-lenina-29 |
| public_name | Fixcar |
| category | auto |
| scope | VILLAGE |
| address | ул. Ленина, 29 |
| latitude | 57.028972 |
| longitude | 28.928888 |
| phone | +7 (921) 607-96-67 |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/fixcar/10518023093/ |
| Yandex ID | 10518023093 |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | none |
| decision | ADD_ACTIVE |

### avtoservis-novorzhevskaya-47 — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | avtoservis-novorzhevskaya-47 |
| public_name | Автосервис |
| category | auto |
| scope | VILLAGE |
| address | ул. Новоржевская, 47 |
| latitude | 57.022064 |
| longitude | 28.946468 |
| phone | null |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/avtoservis/1148040273/ |
| Yandex ID | 1148040273 |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | none |
| decision | ADD_ACTIVE |

### avtomoyka-pushkinskaya-42b — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | avtomoyka-pushkinskaya-42b |
| public_name | Автомойка |
| category | car_wash |
| scope | VILLAGE |
| address | ул. Пушкинская, 42Б |
| latitude | 57.02155 |
| longitude | 28.90255 |
| phone | null |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/avtomoyka/144587691868/ |
| Yandex ID | 144587691868 |
| 2GIS URL | Cannot be verified (captcha) |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | Separate Yandex org from Автосервис 42Б; Yandex card lists village only — house number inferred from Автосервис 42Б block |
| decision | ADD_ACTIVE |

### car-wash-zvyozdnaya — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | car-wash-zvyozdnaya |
| public_name | Автомойка |
| category | car_wash |
| scope | VILLAGE |
| address | ул. Звёздная |
| latitude | 57.019759 |
| longitude | 28.937189 |
| phone | null |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/car_wash/111767984617/ |
| Yandex ID | 111767984617 |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | none |
| decision | ADD_ACTIVE |

### avtozapchasti-lermontova-10 — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | avtozapchasti-lermontova-10 |
| public_name | Автозапчасти |
| category | auto_parts |
| scope | VILLAGE |
| address | ул. Лермонтова, 10 |
| latitude | 57.023774 |
| longitude | 28.935661 |
| phone | +7 (911) 886-76-00 |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/avtozapchasti/104793017590/ |
| Yandex ID | 104793017590 |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | none |
| decision | ADD_ACTIVE |

### zapchasti-lermontova-14a — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | zapchasti-lermontova-14a |
| public_name | Запчасти |
| category | auto_parts |
| scope | VILLAGE |
| address | ул. Лермонтова, 14А |
| latitude | 57.025655 |
| longitude | 28.934556 |
| phone | null |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/zapchasti/140825879681/ |
| Yandex ID | 140825879681 |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | Reviews mention tractor parts |
| decision | ADD_ACTIVE |

### avtozapchasti-pushkinskaya-42a — ADD_ACTIVE

| Поле | Значение |
|------|----------|
| stable_key | avtozapchasti-pushkinskaya-42a |
| public_name | Автозапчасти |
| category | auto_parts |
| scope | VILLAGE |
| address | ул. Пушкинская, 42А |
| latitude | 57.021569 |
| longitude | 28.902262 |
| phone | null |
| opening_hours | null |
| Yandex URL | https://yandex.ru/maps/org/avtozapchasti/94960988832/ |
| Yandex ID | 94960988832 |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | — |
| official/VK | — |
| active status | ACTIVE |
| conflicts | none |
| decision | ADD_ACTIVE |

### avtoremont-lenina — INSUFFICIENT_EVIDENCE

| Поле | Значение |
|------|----------|
| stable_key | avtoremont-lenina |
| public_name | Авторемонт |
| category | auto |
| scope | VILLAGE |
| address | ул. Ленина |
| latitude | 57.0287699 |
| longitude | 28.9293734 |
| phone | null (was +7 (931) 901-56-10 — **Cannot be verified**) |
| opening_hours | null (was OSM-only — **Cannot be verified**) |
| Yandex URL | — |
| Yandex ID | — |
| 2GIS URL | — |
| 2GIS firm ID | — |
| OSM | osm:node/42 removed — **placeholder, not real OSM ID** |
| official/VK | — |
| active status | ACTIVE (legacy row; `seed_as_reference=false`) |
| conflicts | OSM source was false |
| decision | INSUFFICIENT_EVIDENCE |

### universalnaya_masterskaya (search hit) — OUTSIDE_SCOPE

| Поле | Значение |
|------|----------|
| Yandex ID | 144982715626 |
| address on card | Sochi, Demokratichnaya 38А |
| decision | OUTSIDE_SCOPE — not in рп. Пушкинские Горы |

### Техосмотр (186063081537) — not inventoried

Found in Ivanov search; vehicle inspection station — not mapped to Module 3 categories without confirmed auto-repair scope. **Not added.**

## Cannot be verified

- Fresh 2GIS cards for new auto orgs (captcha block).
- `avtoremont-lenina` existence as auto service; phone +7 (931) 901-56-10; OSM node/42.
- Exact house number on Yandex-only «Автомойка» org card (42Б inferred from adjacent Автосервис).
- Village «Универсальная мастерская» as distinct org (search id points to Sochi).
- Эвакуатор services in village (no Yandex results).

## DB migration

**Not required.** `Place.category` is `String(50)` — new values `car_wash`, `auto_parts`, `towing` are string enums in Python only.

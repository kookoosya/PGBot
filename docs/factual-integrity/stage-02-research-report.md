# Stage 2 — Research Report (pre-code)

**Baseline HEAD:** `2e48e1abbfc4b4284f88bef18d22817c8e56a5d8`  
**Research date:** 2026-06-27  
**Scope:** рп. Пушкинские Горы + nearby attractions + district OSM imports

## Method

1. Read-only export of production `/api/v1/places` (40 active entries).
2. Two-pass category search in **Yandex Maps** and **2GIS** (see `stage-02-search-log.md`).
3. Cross-match of name, address, phone, hours, coordinates, active status.
4. Official sources for government, museum, hospital where available.

## Key findings

### Tire shop (OWNER priority)

| Field | Value | Source |
|-------|-------|--------|
| Name | Шиномонтаж | OWNER |
| Address | ул. Аэродромная, 23 | OWNER + 2GIS |
| Phone | +7 (906) 221-03-54 | OWNER |
| 2GIS | https://2gis.ru/firm/70000001075370090 | TWO_GIS |
| Yandex | search card (no stable org slug) | YANDEX |
| Auto2 | **REMOVE** — not an allowed source | — |
| Second phone +7 (981) 783-86-67 | **Do not publish** — not owner-confirmed | — |

### Multisource confirmed (Yandex + 2GIS)

- Магнит ул. Ленина, 42 — Yandex `1613176821`, 2GIS `70000001041826603`
- Магнит ул. Новоржевская, 25 — Yandex `1624883377`, 2GIS `70000001041826641`
- Пятёрочка ул. Ленина, 20А — Yandex `48515124540`, 2GIS `70000001053567895`
- Аптека-А ул. Ленина, 20А — 2GIS `70000001046944968`
- Сбербанк банкомат ул. Ленина, 40 — 2GIS `70000001044502481`
- Святогоръ кафе ул. Ленина, 2 — 2GIS `70000001030949997`
- Дружба гостиница ул. Ленина, 8 — Yandex `1077179086`, 2GIS `70000001030945857`

### New village entries (2GIS / Yandex, not in prior curated seed)

- Пушкин-Парк ресторан, ул. Ленина, 42А — 2GIS `70000001046501223`
- Пушкиногорская центральная районная библиотека, ул. Пушкинская, 3 — 2GIS `70000001046501126`
- Усадьба Тригорская гостиница, ул. Тригорская, 1 — 2GIS `70000001030946214`
- Дом Классика гостевой дом, ул. Пушкинская, 47 — 2GIS `70000001075366027`
- Пушкиногорская школа искусств им. С. С. Гейченко — Yandex `1036116088`
- Автостанция Псковавтотранс, ул. Новоржевская, 30 — Yandex `1103286656`

### Nearby attractions

- Берёзка кафе, Михайловское — 2GIS `70000001044611536` (scope `NEARBY_ATTRACTION`)
- База отдыха Пушкиногорье — 2GIS `70000001040982738` (district/tourism)

### Preserved without deletion

- OSM imports (Продмаг №7, Авторемонт, ФАП) — kept; missing Yandex/2GIS card is **not** grounds for removal.
- Official entries (музей, монастырь, администрация, больница) — unchanged primary sources.
- Production hotels from legacy seed — **not removed** in this stage; curated inventory focuses on map-verified village directory.

### Conflicts / Cannot be verified

- **Кафе «Пушкинъ»** (пл. Ленина, 3) vs **Святогоръ** (ул. Ленина, 2) — separate cards; both kept.
- **АЗС Новоржевская, 31** — Yandex search only; 2GIS card not matched in pass 2 → `YANDEX_ACTIVE`.
- **Raypo Тригорская, 3** — Yandex shows intermittent closed hours; kept active pending owner confirmation.
- **MFC** — nearest in Pskov, not in village; no village MFC card added.

### Pushkin quotes audit

Repository-wide grep: forbidden misquotes **absent**. Verified set in `shared/pushkin_quotes.json` and hero in `shared/portal_copy.json` — all with RVB `source_url`, work, year.

### Events (read-only)

No parser or import changes. Source list documented in `stage-02-events-source-audit.md`. Production API intermittently unreachable from research host; audit based on codebase registry + existing tests.

## Planned code changes (minimal)

1. Migrate `source_types` URLs → structured `sources[]`.
2. Add `category_status` per entry.
3. Enrich 2GIS / Yandex IDs; add new multisource entries above.
4. Remove Auto2 from tire shop; remove unverified second phone from public fields.
5. Update `verification_label()` for TWO_GIS and multisource public labels.
6. Sync `backend/app/data/` and `docs/factual-integrity/` inventories.
7. Expand stage-02 integrity tests.

**STAGE 2 code changes not started until this report was written.**

# Module 12 — production point verification

**Baseline SHA:** `5329246b93304b7919ba75f8c667e098c102b21c`  
**Scope:** close Module 10 «Cannot verify» items for шиномонтаж, КДЦ, столовая на Турбазе.  
**Module 13:** not started.

## Pre-change entity table

| Entity | Stable key | Prod id (2026-07-04) | Category | Address | Scope | Active | Public API visible | Search visible | Map visible |
|--------|------------|----------------------|----------|---------|-------|--------|--------------------|----------------|-------------|
| Шиномонтаж | `shinomontazh-aerodromnaya-23` | **326** | tyre | ул. Аэродромная, 23 | VILLAGE | yes | yes | шиномонтаж, Аэродромная, `category=tyre` | yes |
| КДЦ (МБУК) | `kdc-sadovaya-1` | **371** | culture | ул. Садовая, 1 | VILLAGE | yes | yes | культур, Садовая, `category=culture`; **КДЦ → 0** (alias gap) | yes |
| Турбаза «Пушкиногорье» | `turbaza-pushkinogorye` | **372** | hotel | микрорайон Турбаза | VILLAGE | yes | yes | Турбаза, Пушкиногорье | yes |
| Столовая | `stolovaya-pushkinogorye-turbaza` | **373** | restaurant | ул. Турбаза | VILLAGE | yes | yes | столовая, Турбаза, Пушкиногорье, `category=restaurant` | yes |

Module 10 cited place id **327** for шиномонтаж; production recount on 2026-07-04 shows tyre at id **326** (id drift between audits — coordinates and address match inventory).

## Production requests

Base: `https://pushkinskie-gory.xyz`

| # | URL | Status | total | IDs | Matched names / notes |
|---|-----|--------|-------|-----|------------------------|
| H | `/health` | 200 | — | — | `git_commit`: `5329246` |
| 1 | `/api/v1/places?category=tyre&scope=VILLAGE` | 200 | 1 | [326] | Шиномонтаж, ул. Аэродромная, 23 |
| 2 | `/api/v1/places?search=шиномонтаж&scope=VILLAGE` | 200 | 1 | [326] | same |
| 3 | `/api/v1/places?search=Аэродромная&scope=VILLAGE` | 200 | 2 | [361, 326] | includes tyre at 23 |
| 4 | `/api/v1/places/326` | 200 | — | 326 | phone `+7 (906) 221-03-54`, `verification_status`: `OWNER_CONFIRMED`, `verification_label`: «Подтверждено владельцем» |
| 5 | `/api/v1/places?search=КДЦ&scope=VILLAGE` | 200 | **0** | [] | alias not in name/address (pre-fix) |
| 6 | `/api/v1/places?search=культур&scope=VILLAGE` | 200 | 1 | [371] | МБУК «Культурно-досуговый центр» |
| 7 | `/api/v1/places?search=Садовая&scope=VILLAGE` | 200 | 1 | [371] | ул. Садовая, 1 |
| 8 | `/api/v1/places?category=culture&scope=VILLAGE` | 200 | 4 | [336, 371, 345, 337] | includes KDC at 371 |
| 9 | `/api/v1/places?search=столовая&scope=VILLAGE` | 200 | 1 | [373] | Пушкиногорье, столовая |
| 10 | `/api/v1/places?search=Турбаза&scope=VILLAGE` | 200 | 2 | [372, 373] | hotel + restaurant |
| 11 | `/api/v1/places?search=Пушкиногорье&scope=VILLAGE` | 200 | 2 | [372, 373] | lodging cluster |
| 12 | `/api/v1/places?category=restaurant&scope=VILLAGE` | 200 | 2 | [350, 373] | includes столовая |
| 13 | `/api/v1/places?category=hotel&scope=VILLAGE` | 200 | 4 | [353, 351, 372, 352] | includes турбаза |

## 1. Шиномонтаж Аэродромная, 23

| Field | Value |
|-------|-------|
| Inventory key | `shinomontazh-aerodromnaya-23` |
| Production id | **326** |
| Address | ул. Аэродромная, 23 |
| Phone (inventory) | `+7 (906) 221-03-54` (`phone_status`: `OWNER_CONFIRMED`) |
| Phone (production detail) | `+7 (906) 221-03-54` ✓ |
| Owner evidence | `existence_status` / `phone_status`: `OWNER_CONFIRMED`; source `owner:project` |
| Public API fields | `verification_status`, `verification_label`, `verification_source_url`, `phone` **are exposed** by contract (`PlaceResponse` / `build_place_response`) |
| Production verification | `OWNER_CONFIRMED`, label «Подтверждено владельцем» |

**Decision:** `KEEP_VERIFIED` — Module 10 gaps were audit-time timeouts / stale id; live API confirms owner status and phone.

## 2. КДЦ

| Field | Value |
|-------|-------|
| Inventory key | `kdc-sadovaya-1` |
| Production id | **371** |
| Public name | МБУК «Культурно-досуговый центр» |
| Alias | «КДЦ Пушкиногорского района» |
| Address | ул. Садовая, 1 |
| Category | `culture` |
| Event source only? | **No** — active seeded map place; distinct from `nkc-pushkinskie-gory` (museum NKC, б-р Гейченко) |
| Production visibility | culture category, search by «культур» / «Садовая» |
| Search «КДЦ» before fix | **0** — search matched only `name` and `address`; alias lived only in inventory |

**Root cause:** alias not copied into searchable DB fields.

**Decision:** `KEEP_VERIFIED` as map point + `FIX_SEARCH_VISIBILITY` — append aliases to seeded `description` and include `description` in place search filter.

## 3. Столовая на Турбазе

| Field | Value |
|-------|-------|
| Inventory key | `stolovaya-pushkinogorye-turbaza` |
| Production id | **373** |
| Public name | Пушкиногорье, столовая |
| Address | ул. Турбаза |
| Category | `restaurant` |
| Related | `turbaza-pushkinogorye` id **372** (hotel, микрорайон Турбаза) — separate Yandex org |
| Duplicate analysis | Same brand vicinity; **separate** Yandex card `83521990347`; not merged per Module 4 |
| Production visibility | search «столовая», «Турбаза», «Пушкиногорье»; `category=restaurant` |

**Decision:** `KEEP_VERIFIED` — separate public map point; not a sub-feature of турбаза only.

## Changes in this module

| File | Change |
|------|--------|
| `backend/app/services/place_inventory.py` | `build_public_description`: prepend aliases as «Также: …» for search indexing |
| `backend/app/services/place/search.py` | search filter also matches `Place.description` |
| `backend/tests/test_module12_production_points.py` | Module 12 targeted tests |
| `docs/factual-integrity/module-12-production-point-verification.md` | this audit |

**Inventory JSON:** unchanged (data already correct).  
**Schools / map bbox / clustering / Афиша / unrelated orgs:** untouched.

### Why minimal

- Tyre and столовая required no data fixes — production already matched inventory.
- KDC needed only search-index gap fix, not a new place or category change.
- Public API already exposes verification fields; Module 10 «may not expose» was superseded by `test_public_api_includes_verification_fields` and live detail on id 326.

## Tests

- `backend/tests/test_module12_production_points.py` — inventory, tyre owner/phone, KDC alias search (postgres), столовая search, school count regression, map stats sum.
- Existing suites: `test_map_reference_integrity_stage02.py`, `test_osint_candidates_inventory.py`, `test_module11_school_reconciliation.py`.

## Cannot be verified

_None for the three Module 12 scope items after production API confirmation._

(Residual Module 10 items outside scope — e.g. 4h event re-sync, React remount — remain in Module 10 audit.)

## Module status

- **Module 12:** complete after deploy confirms `search=КДЦ` returns id 371+.
- **Module 13:** not started.

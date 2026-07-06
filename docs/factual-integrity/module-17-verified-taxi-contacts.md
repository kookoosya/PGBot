# Module 17 — Verified Taxi Contacts OSINT + Public UI

**Status:** COMPLETE  
**Baseline:** `badb51a4ee6b763ade6f091feba55c0a9be32c79`  
**Final:** `2e154d723d1401b3ca77738afb89014647508e56`  
**Scenario:** **NOT_FOUND** — no taxi contact met verification threshold  
**Branch:** `main`

## Production baseline (pre-change)

| Metric | Value | Notes |
|--------|------:|-------|
| `/health` | `badb51a` or `c37cc2d` | docs-only delta between commits |
| Verified taxi phones (API `/places/taxi`) | **0** | `[]` |
| Numbers tab verified place phones | **20** | Module 16 contract |
| Taxi tab | empty-state | «Проверенные номера такси пока не добавлены» |
| `catalog_places` | **45** | unchanged |
| `routes` | **11** | unchanged |

Production curl from Windows timed out (SSL exit 35); deploy smoke on prior module confirms API contract. **Cannot be verified** live from agent host — regression locked by tests.

## Repo taxi candidates

| candidate | current status | source in repo | phone | address | reason rejected/accepted |
|-----------|----------------|----------------|-------|---------|------------------------|
| Work.Taxi | NOT_PUBLIC_SERVICE | `work-taxi-candidate` inventory | null | null | Module 4: no Yandex org; driver-recruiting partner, not passenger dispatch |
| Наше такси | REJECTED (old TAXI_SEED) | `stage-01-map-reference-audit.md` | +7 (921) 000-28-28 | — | PLACEHOLDER pattern; deactivated stage 1 |
| Такси Комфорт | REJECTED (old TAXI_SEED) | `stage-01-map-reference-audit.md` | 60-18-18 / +7 (931) 905-50-50 | — | UNVERIFIED; no Yandex/2GIS passenger card in village |
| Грузоперевозки (Дмитрий) | REJECTED | old TAXI_SEED | +7 (911) 354-70-24 | — | cargo; single aggregator |
| `TAXI_SEED` | **empty** | `pushkin_places_seed.py` | — | — | intentional since stage 2 |
| Автовокзал | KEEP (transport, no phone) | `avtovokzal-novorzhevskaya-30` | null | ул. Новоржевская, 30 | transport place; phone UNVERIFIED |

## OSINT search queries (2026-07-06)

1. `такси Пушкинские Горы телефон`
2. `такси Пушкиногорье телефон`
3. `такси Пушкиногорский район телефон`
4. `Пушкинские Горы такси`
5. `Пушкиногорье такси`
6. `Пушкинские Горы трансфер телефон`
7. `такси Пушкинские Горы Псковская область`
8. `Work.Taxi Пушкинские Горы`
9. `такси до Пушкинских Гор`
10. `Пушкинские Горы автовокзал телефон`
11. `Пушкинские Горы перевозки телефон`
12. `site:yandex.ru/maps "Такси Комфорт" Пушкинские Горы`
13. `"Такси Комфорт" "Пушкинские Горы" site:vk.com`

## Evidence table

| phone | name | source URL | source type | freshness | address/area | confidence | decision |
|-------|------|------------|-------------|-----------|--------------|------------|----------|
| 60-18-18 / +7 (8112) 60-18-18 | Такси «Комфорт» | https://meconnect.ru/taxi.pg | local directory | undated | Пушкинские Горы (no street) | LOW–MEDIUM | **INSUFFICIENT_EVIDENCE** |
| +7 (931) 905-50-50 | Такси «Комфорт» | https://intaxi.ru/pushkinskiye-gory/komfort/ | aggregator template | 2025-03-11 | settlement only | LOW | **INSUFFICIENT_EVIDENCE** |
| +7 (8112) 60-18-18, +7 (921) 000-28-28 | Комфорт / Наше Такси | https://taxitelephone.ru/pskovskaya-oblast/pushkinskie-gory | aggregator | undated | Пушкинские Горы | LOW | **INSUFFICIENT_EVIDENCE** |
| +7 (921) 000-28-28 | Наше такси | https://taxi-pg.orgs.biz/ | self-registered directory | undated | Пушкинские Горы | LOW | **KEEP_REJECTED** (PLACEHOLDER) |
| +7 (911) 354-70-24 | Грузоперевозки | taxitelephone.ru | aggregator | undated | Пушкинские Горы | LOW | **REJECT** (cargo, not passenger taxi) |
| +7 (904) 888-6-777 | Work.Taxi | https://2gis.ru/firm/70000001055391624 | 2GIS org card | live 2026-07-06 | рп. Пушкинские Горы (no street) | MEDIUM | **KEEP_REJECTED** — Yandex Go partner / driver onboarding, not verified passenger dispatch |
| +7 (904) 888-6-777 | Work.Taxi | https://work.taxi/ | corporate site | live | multi-city franchise | MEDIUM | **KEEP_REJECTED** — regional recruiter, not local taxi directory |
| +7 (921) 585-07-85 | intercity transfer | transfer aggregator | aggregator | — | Pskov ↔ PG | LOW | **OUT_OF_SCOPE** |

### Why no ADD_VERIFIED_TAXI

Project rules require **HIGH** (official site, Yandex/2GIS+phone+location, VK official, multiple independent sources) or **MEDIUM** (local catalog + second independent corroboration).

- **Такси Комфорт:** only meConnect local page + aggregators repeating the same numbers; **no Yandex Maps org** in Пушкинские Горы; no verified VK official page with matching phone found.
- **Наше такси:** `000-28-28` matches stage-1 PLACEHOLDER; orgs.biz self-page only.
- **Work.Taxi:** 2GIS card exists but service is **official Yandex Go partner / driver fleet**, explicitly rejected in Module 4/10/14/16 as `NOT_PUBLIC_SERVICE`; corporate phone is not a verified village passenger taxi line.

## Work.Taxi decision

**KEEP_REJECTED / NOT_PUBLIC_SERVICE**

- Inventory: `work-taxi-candidate`, `decision: NOT_PUBLIC_SERVICE`, no coords, `seed_as_reference: false`
- 2GIS lists location «рп. Пушкинские Горы» and partial phone `+7 904 888…` but no street address; primary business is driver recruitment for Yandex Go (work.taxi)
- Does not satisfy passenger taxi directory contract; user rule forbids adding Work.Taxi without verified passenger dispatch evidence

## Catalog / contact-only model

| Item | Value |
|------|-------|
| Catalog count changed | **no** — remains **45** |
| `TAXI_SEED` changed | **no** — remains `[]` |
| Contact-only taxi added | **no** |
| UI change | **none** — empty-state retained |

## Accepted taxi contacts

**None.**

## Hidden / rejected (unchanged)

All candidates above remain rejected or insufficient. Module 16 numbers tab unchanged (20 verified place phones + 5 emergency).

## Tests

- `backend/tests/test_module17_verified_taxi_contacts.py`
- `frontend/src/pages/map/TaxiPanel.test.tsx` (extended)
- `frontend/src/pages/map/module17TaxiIntegrity.test.ts`

## Changed files

- `docs/factual-integrity/module-17-verified-taxi-contacts.md` (this file)
- `backend/tests/test_module17_verified_taxi_contacts.py`
- `frontend/src/pages/map/TaxiPanel.test.tsx`
- `frontend/src/pages/map/module17TaxiIntegrity.test.ts`

## Cannot be verified

- Live production UI screenshots (`docs/screenshots/module-17-production/`) — not captured in agent session
- Live production `/health` from Windows host — curl SSL timeout; use deploy smoke
- Whether `60-18-18` is currently answered by a live local dispatch — no independent primary source
- Whether `+7 (921) 000-28-28` is a real mobile line — pattern flagged PLACEHOLDER in stage 1
- CI run ID from GitHub API locally

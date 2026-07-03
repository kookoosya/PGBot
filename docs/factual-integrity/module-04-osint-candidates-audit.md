# Module 4 — OSINT candidates audit

**Audit date:** 2026-07-03  
**Baseline git:** `e87212924d6e37f98e01bd5a1884b0d2abb5c92e`  
**Inventory baseline (report):** `2e48e1abbfc4b4284f88bef18d22817c8e56a5d8` (stage-02-research-report)

## Source OSINT reports

| Path | Role |
|------|------|
| `docs/factual-integrity/stage-02-research-report.md` | Primary candidate list (MFC, база отдыха, Raypo) |
| `docs/factual-integrity/stage-02-search-log.md` | Pass 1–2 category sweeps |
| `docs/factual-integrity/module-03-extra-search.json` | Sieszka `171350854821`, столовая `83521990347` |
| `docs/factual-integrity/stage-02-place-inventory.json` | Pre-module-4 inventory (46 places) |
| `backend/app/services/lodging_seed.py` | Legacy hotel/turbaza mentions (not curated) |

**Module 4 verification artifacts (local, not committed):** `module-04-verify-raw.json`, `module-04-verify2-raw.json`

## Candidate work table

| Кандидат | Текущий статус | Yandex | 2GIS | Scope | Возможный дубль | Требуется проверка |
|----------|----------------|--------|------|-------|-----------------|--------------------|
| МФЦ «Мои документы» | ADD_ACTIVE | `121679162119` | — | VILLAGE | administratsiya-lenina-6 (same building) | Отдельная услуга |
| Съешка | ADD_ACTIVE | `171350854821` | — | VILLAGE | kafe-pushkin, svyatogor | Переезд с 12А |
| Work.Taxi | NOT_PUBLIC_SERVICE | — | — | — | taxi seed empty | Физическая точка |
| КДЦ (МБУК) | ADD_ACTIVE | `1057172663` | — | VILLAGE | nkc-pushkinskie-gory | Отдельный адрес |
| Турбаза «Пушкиногорье» | ADD_ACTIVE | `130921547558` | `70000001040982738`* | VILLAGE | lodging_seed dup | Scope в посёлке |
| Отдел закупок РАЙПО | NOT_PUBLIC_SERVICE | `35355226565` | — | VILLAGE | raypo-trigorskaya-3 | Публичная услуга |
| Пушкиногорье, столовая | ADD_ACTIVE | `83521990347` | — | VILLAGE | turbaza complex | Категория |
| Гостиница «Пушкиногорская» | INSUFFICIENT_EVIDENCE | — | — | VILLAGE | druzhba-hotel | Org card |
| РАЙПО Тригорская, 3 | KEEP_EXISTING | `11910956685` | — | VILLAGE | — | Уже в inventory |
| Старая карточка Съешка 12А | DUPLICATE_CONFIRMED | `115657929994` | — | — | sieszka-69 | Переезд |

\*2GIS firm page blocked by captcha during Module 4 run; ID from stage-02-research-report only — not used as live source in inventory.

## Yandex Maps queries (2026-07-03)

1. `МФЦ Пушкинские Горы`
2. `Съешка Пушкинские Горы`
3. `Sieszka Пушкинские Горы`
4. `Work.Taxi Пушкинские Горы`
5. `КДЦ Пушкинские Горы`
6. `база отдыха Пушкиногорье Пушкинские Горы`
7. `отдел закупок РАЙПО Пушкинские Горы`
8. `столовая Пушкиногорье Пушкинские Горы`
9. `Гостиница Пушкиногорская Пушкинские Горы`
10. `дом культуры Пушкинские Горы`

Direct org pages opened: `sieszka/171350854821`, `pushkinogorye_stolovaya/83521990347`, `mfts_moi_dokumenty/121679162119`, `kulturno_dosugovy_tsentr/1057172663`, `pushkinogore/130921547558`, `otdel_zakupok_raypo/35355226565`.

## 2GIS queries

- `firm/70000001040982738` — captcha blocked (Cannot verify live fields).

## Official sources

| Candidate | URL | Supports |
|-----------|-----|----------|
| МФЦ | https://mfc.pskov.ru | government service network |
| КДЦ | https://kdc-pushgory.ru | MBUK culture center |
| Турбаза | https://pgtur.ru | hotel/base existence, phone |

## Decisions

### ADD_ACTIVE (inventory `RESTORE`, `seed_as_reference: true`)

| stable_key | public_name | category | address |
|------------|-------------|----------|---------|
| `mfc-lenina-6` | МФЦ «Мои документы» | government | ул. Ленина, 6 |
| `sieszka-pushkinskaya-69` | Съешка | cafe | ул. Пушкинская, 69 |
| `kdc-sadovaya-1` | МБУК «Культурно-досуговый центр» | culture | ул. Садовая, 1 |
| `turbaza-pushkinogorye` | Пушкиногорье | hotel | микрорайон Турбаза |
| `stolovaya-pushkinogorye-turbaza` | Пушкиногорье, столовая | restaurant | ул. Турбаза |

### KEEP_EXISTING

| stable_key | Reason |
|------------|--------|
| `raypo-trigorskaya-3` | Public РАЙПО shop already curated |
| `nkc-pushkinskie-gory` | Museum NKC — separate from KDC |
| All Module 1–3 entries | Out of Module 4 scope |

### DUPLICATE_CONFIRMED

| Candidate | Duplicate of | Proof |
|-----------|--------------|-------|
| Yandex `sieszka/115657929994` (ул. Пушкинская, 12А) | `sieszka-pushkinskaya-69` | Same slug; Yandex «Организация переехала» → ул. 69 |

### NOT_PUBLIC_SERVICE

| stable_key | Reason |
|------------|--------|
| `work-taxi-candidate` | Zero Yandex org cards; no local office |
| `raypo-otdel-zakupok` | Internal procurement; not citizen-facing retail |

### INSUFFICIENT_EVIDENCE

| stable_key | Reason |
|------------|--------|
| `gostinitsa-pushkinogorskaya` | No stable Yandex org at Новоржевская 18; lodging_seed only |

### OUTSIDE_SCOPE

_None in Module 4 batch (турбаза confirmed inside village microdistrict)._

### CONFLICT_REVIEW

_None unresolved._

### CLOSED_CONFIRMED

_None._

### Cannot be verified

- 2GIS live card for `70000001040982738` (captcha).
- Full weekly hours for MFC, Sieszka, столовая (Yandex cards lack schedule).
- Гостиница «Пушкиногорская» coordinates and active status.

## Named candidate summaries

### МФЦ

**ADD_ACTIVE.** Village MFC at ул. Ленина, 6 (same building as administration, separate public desk). Yandex `121679162119`, phone `+7 (8112) 29-92-98`, mfc.pskov.ru. Accepts citizens per reviews and category.

### «Съешка»

**ADD_ACTIVE.** Cafe at ул. Пушкинская, 69 (relocated from 12А). Yandex `171350854821`. Not duplicate of Пушкинъ or Святогоръ.

### Work.Taxi

**NOT_PUBLIC_SERVICE.** Query returned zero org cards — no physical point to seed.

### КДЦ

**ADD_ACTIVE** (not duplicate of НКЦ). MBUK at ул. Садовая, 1; phone `2-33-03`; kdc-pushgory.ru. NKC remains at б-р Гейченко, 1 with pushkinland.ru.

### Турбаза «Пушкиногорье»

**ADD_ACTIVE**, scope **VILLAGE**, category **hotel**. Yandex `130921547558`, address микрорайон Турбаза, pgtur.ru.

### Отдел закупок РАЙПО

**NOT_PUBLIC_SERVICE.** Yandex card at Новоржевская 45 is back-office; public shops remain `raypo-trigorskaya-3`.

### Столовая

**ADD_ACTIVE** as **restaurant** at ул. Турбаза, Yandex `83521990347`.

## Inventory summary after Module 4

| Metric | Value |
|--------|-------|
| total_candidates | 56 |
| village_active | 45 |
| not_public_service | 2 |
| insufficient_evidence | 1 |
| rejected (total) | 2 |

## Module 5

**NOT STARTED.**

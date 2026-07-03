# Module 11 — Village school count reconciliation

**Baseline:** `383536fe36cfe11a6d4f603095e0e1f9529e5b34`  
**Decision:** `KEEP_BOTH_VERIFIED`  
**Production `school` count:** `2` (unchanged, correct)

## 1. Why stats shows `school: 2`

`scope=VILLAGE` + `category=school` + `seed_as_reference=true` + active inventory yields **two** entries:

| # | stable_key | public_name | address | yandex_id |
|---|------------|-------------|---------|-----------|
| 1 | `school-1-lenina-30` | Пушкиногорская средняя общеобразовательная школа имени А.С. Пушкина | ул. Лермонтова, 13 | `1040866154` |
| 2 | `art-school-geychenko-pushkinskaya-3` | Пушкиногорская школа искусств им. С. С. Гейченко | ул. Пушкинская, 3 | `1036116088` |

**Not** the sanatorium school-interhat. That institution is **not** in inventory and **not** seeded.

## 2. Main school (`school-1-lenina-30`)

| Field | Value |
|-------|-------|
| Address | ул. Лермонтова, 13 |
| Phone | +7 (81146) 2-13-30 |
| Website | http://pushschool.ucoz.ru |
| Coordinates | 57.024842, 28.933864 |
| Status | ACTIVE, MULTISOURCE_CONFIRMED |

**Sources**

- Yandex Maps org `1040866154`
- Official site http://pushschool.ucoz.ru
- Municipality schools directory: https://pushgory.gosuslugi.ru/spravochnik/shkoly/ — «МБОУ Пушкиногорская СОШ имени А.С. Пушкина», Лермонтова 13, +7 (81146) 2-13-30

**Legacy:** `ул. Ленина, 30` in `conflict_notes` only — erroneous old address, not a second public record.

## 3. Second school (`art-school-geychenko-pushkinskaya-3`)

| Field | Value |
|-------|-------|
| Type | МБО ДО (дополнительное образование), not general SOSH |
| Address | ул. Пушкинская, 3 |
| Coordinates | 57.0251, 28.9142 |
| Phone | UNVERIFIED (official +7 (81146) 2-37-55 not published — Yandex card has no confirmed phone) |
| Status | ACTIVE, MULTISOURCE_CONFIRMED |

**Sources**

- Yandex Maps org `1036116088`
- Municipality subordinate orgs: https://pushgory.gosuslugi.ru/ofitsialno/struktura-munitsipalnogo-obrazovaniya/munitsipalnye-podvedomstvennye-organizatsii/ — МБО ДО «ШИ имени С.С. Гейченко», Пушкинская 3
- RBC / Tochka registry: ОГРН `1156027004495`, active as of 2026

## 4. Sanatorium (investigated, not in production)

| Field | Value |
|-------|-------|
| Name | ГБОУ «Пушкиногорская санаторная школа-интернат» |
| Official address | **ул. Ленина, 5** (not 30) |
| Phone | +7 (81146) 2-13-29 |
| Status | Active separate legal entity (ОГРН `1026002142363`) |

Listed on municipality schools page alongside SOSH. **Intentionally excluded** from portal seed (Module 5): no stable_key, `seed_as_reference` absent.

**Conclusion:** Sanatorium does **not** explain `school: 2`. It is a third school in the settlement, outside current catalog scope.

## 5. Duplicate analysis

| Hypothesis | Result |
|------------|--------|
| Main SOSH duplicate of art school | **No** — different legal entities, addresses, Yandex IDs |
| Main SOSH duplicate at Lenina 30 | **No** — legacy address only in notes |
| Art school = sanatorium | **No** — Pushkinskaya 3 vs Lenina 5 |
| Sanatorium in production | **No** — not in inventory seed |
| Two real village schools in catalog | **Yes** |

## 6. Decision rules applied

Both seeded schools are real, active, separate institutions → **KEEP_BOTH_VERIFIED**, keep `school: 2`.

## 7. Changes made

| File | Change |
|------|--------|
| `backend/app/data/stage-02-place-inventory.json` | Art school: official municipality source, MULTISOURCE_CONFIRMED, conflict_notes; main school: clarified verification_note |
| `docs/factual-integrity/stage-02-place-inventory.json` | Identical copy |
| `backend/tests/test_module11_school_reconciliation.py` | Targeted tests |
| This audit | — |

Main school address **unchanged** (already verified Лермонтова 13).

## 8. Cannot be verified

- Art school public phone (+7 (81146) 2-37-55) on portal — official municipality lists it; Yandex org card does not confirm → `phone_status: UNVERIFIED`, phone not published.
- Production `/api/v1/places` live fetch from agent network — **Cannot be verified** locally (timeout); rely on inventory seed logic + post-deploy smoke (CI smoke-prod job).

## 9. Expected production after deploy

- `/health` → new commit SHA
- `school: 2` in village stats
- Two map cards: SOSH (Лермонтова 13) + art school (Пушкинская 3)
- No school at ул. Ленина, 30
- Total village catalog: 45

---

**MODULE 11 decision:** `KEEP_BOTH_VERIFIED`  
**MODULE 12:** NOT STARTED

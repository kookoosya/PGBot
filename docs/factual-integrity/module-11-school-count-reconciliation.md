# Module 11 — Village school count reconciliation

**Baseline:** `550eb482e5d44ab3ccc239e5fc3f24f1f65f329b`

**Prior erroneous closure:** отчёт с baseline `383536f` и SHA `75888de` закрыт преждевременно; модуль переоткрыт с baseline rules-commit.
**Decision:** `KEEP_BOTH_VERIFIED`  
**Status:** production verification pending new module commit HEAD

## Production school records (pre-step-12, `/health` = `75888de`)

| prod id | stable_key | public_name | address | coordinates | yandex_id |
|---------|------------|-------------|---------|-------------|-----------|
| 344 | `school-1-lenina-30` | Пушкиногорская средняя общеобразовательная школа имени А.С. Пушкина | ул. Лермонтова, 13 | 57.024842, 28.933864 | `1040866154` |
| 355 | `art-school-geychenko-pushkinskaya-3` | Пушкиногорская школа искусств им. С. С. Гейченко | ул. Пушкинская, 3 | 57.0251, 28.9142 | `1036116088` |

API: `/api/v1/places?scope=VILLAGE&category=school` → `total: 2`.
Нет записи с адресом ул. Ленина, 30.

## 1. Why stats shows `school: 2`

`scope=VILLAGE` + `category=school` + `seed_as_reference=true` + active inventory → **две** записи (см. таблицу выше).

**Не** санаторная школа-интернат (ул. Ленина, 5) — отдельное учреждение, **не** в seed.

## 2. Main school (`school-1-lenina-30`)

| Field | Value |
|-------|-------|
| Address | ул. Лермонтова, 13 |
| Phone | +7 (81146) 2-13-30 |
| Website | http://pushschool.ucoz.ru |
| decision | RESTORE |
| active_status | ACTIVE |

**Sources:** Yandex `1040866154`; http://pushschool.ucoz.ru; [municipality schools](https://pushgory.gosuslugi.ru/spravochnik/shkoly/) — МБОУ СОШ им. А.С. Пушкина, Лермонтова 13.

**Legacy:** ул. Ленина, 30 только в `conflict_notes` — ошибочный старый адрес, не вторая карточка.

## 3. Second school (`art-school-geychenko-pushkinskaya-3`)

| Field | Value |
|-------|-------|
| Type | МБО ДО дополнительного образования |
| Address | ул. Пушкинская, 3 |
| Phone | null (`phone_status: UNVERIFIED`) |
| decision | RESTORE |
| active_status | ACTIVE |

**Sources:** Yandex `1036116088`; [municipality orgs](https://pushgory.gosuslugi.ru/ofitsialno/struktura-munitsipalnogo-obrazovaniya/munitsipalnye-podvedomstvennye-organizatsii/) — МБО ДО ШИ им. С.С. Гейченко, Пушкинская 3; ОГРН `1156027004495` (active).

## 4. Sanatorium (out of scope for count)

ГБОУ «Пушкиногорская санаторная школа-интернат» — ул. **Ленина, 5**, +7 (81146) 2-13-29.
[Official directory](https://pushgory.gosuslugi.ru/spravochnik/shkoly/) lists it separately from SOSH.
Not in inventory seed → does **not** contribute to `school: 2`.

## 5. Duplicate analysis

| Hypothesis | Result |
|------------|--------|
| SOSH duplicate of art school | **No** — different entities, addresses, Yandex IDs |
| Second record = Lenina 30 legacy | **No** — no public address Lenina 30 |
| Second record = sanatorium | **No** — sanatorium at Lenina 5, not seeded |
| Two real separate schools in catalog | **Yes** |

## 6. Decision

**KEEP_BOTH_VERIFIED** — сохранить `school: 2`; не удалять школу искусств; не менять адрес СОШ.

## 7. Inventory changes (from baseline `550eb48` tree)

Already present in tree (commits `75888de` ancestry):

- Art school: `OFFICIAL_WEBSITE` municipality source, `MULTISOURCE_CONFIRMED`, `conflict_notes`
- Main school: `verification_note` clarifies pair SOSH + art school vs sanatorium

## 8. Cannot be verified

- Art school phone on portal — municipality lists +7 (81146) 2-37-55; Yandex org card unconfirmed → not published.
- Local `/api/v1/places/stats?scope=VILLAGE` — intermittent timeout from agent network; use places list + deploy smoke.

## 9. Targeted tests

`backend/tests/test_module11_school_reconciliation.py` — 11 tests; plus Module 5 school tests in `test_core_conflicts_inventory.py`.

---

**MODULE 11:** NOT COMPLETE until post-deploy verification at final HEAD
**MODULE 12:** NOT STARTED

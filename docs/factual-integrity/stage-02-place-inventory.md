# Stage 02 — Place inventory audit

**Baseline SHA:** `2a2052184eedc8ed6a359ffa4e1b48382bb228bf`  
**Inventory generated:** see `stage-02-place-inventory.json`  
**Passes:** 2 (no new unique village orgs on second pass)

## Summary

| Metric | Count |
|--------|------:|
| Total candidates in registry | 28 |
| Village (KEEP/RESTORE) | 24 |
| Nearby attractions | 2 |
| Municipal district (OSM only) | 2 |
| Restored from Stage 1 quarantine | 18 |

Machine-readable registry: [`stage-02-place-inventory.json`](stage-02-place-inventory.json)

## Owner-confirmed: шиномонтаж ул. Аэродромная, 23

| Field | Value | Status |
|-------|-------|--------|
| Name | Шиномонтаж | OWNER_CONFIRMED |
| Address | ул. Аэродромная, 23 | YANDEX_ACTIVE / 2GIS |
| Coordinates | 57.0173, 28.9335 | MULTISOURCE |
| Phone | +7 (906) 221-03-54 | OWNER_CONFIRMED |
| Hours | — | Cannot be verified |
| Yandex | search card | YANDEX_ACTIVE |
| 2GIS | https://2gis.ru/firm/70000001075370090 | YANDEX_ACTIVE |

## Restored organizations (Stage 1 → Stage 2)

Пятёрочка (Ленина 20А), Пятёрочка (Пушкинская 11), Магнит ×2, М.Косметик, Аптека-А ×2, РАЙПО, АЗС, шиномонтаж, администрация, почта, Сбербанк ATM, автовокзал, кафе, школа, НКЦ, парковка музея, усадьба (nearby), парковка Трёх Сосен.

## Not deactivated (no CLOSED_CONFIRMED)

No mass deactivation. Placeholder phones removed; unknown phones left `null`.

## Backup

- `docs/factual-integrity/backups/places-before-stage02-api.json` — production API export (SSH backup blocked: ETIMEDOUT)

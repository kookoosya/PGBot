# Module 5 — Core conflicts audit (AZS, school, hospital)

**Audit date:** 2026-07-03  
**Baseline git:** `7e9e482432f837e8e5842dce45647a7024be41ff`  
**Verification artifact (local, not committed):** `module-05-verify-raw.json`

## Decision summary

| Object | stable_key | Decision | Public name | Address |
|--------|------------|----------|-------------|---------|
| АЗС | `azs-pskovnefteprodukt-novorzhevskaya-31` | UPDATE_VERIFIED + DUPLICATE_CONFIRMED aliases | Сургутнефтегаз | ул. Новоржевская, 31 |
| Школа | `school-1-lenina-30` | UPDATE_VERIFIED | Пушкиногорская СОШ им. А.С. Пушкина | ул. Лермонтова, 13 |
| Больница | `hospital-pushkinogorsky-filial` | UPDATE_VERIFIED | Пушкиногорская межрайонная больница | ул. Ленина, 41 |

---

## 1. АЗС — «АЗС №1» vs «АЗС №31» / Псковнефтепродукт

### Исходные записи

| stable_key | Было | Противоречие |
|------------|------|--------------|
| `azs-pskovnefteprodukt-novorzhevskaya-31` | «АЗС Псковнефтепродукт», search URL, без yandex_id | OSINT: «АЗС №1» vs «№31»; неверный бренд; нет org card |

### Yandex queries (2026-07-03)

- `АЗС Пушкинские Горы`
- `АЗС №1 Пушкинские Горы`
- `АЗС Новоржевская 31 Пушкинские Горы`
- `Псковнефтепродукт АЗС Пушкинские Горы`

Все ведут на одну карточку: **Сургутнефтегаз** `108531110258`.

### Подтверждённые поля

| Поле | Значение | Источник |
|------|----------|----------|
| existence | ACTIVE | Yandex org |
| public_name | Сургутнефтегаз | Yandex org |
| category | gas | Yandex |
| address | ул. Новоржевская, 31 | Yandex org |
| coordinates | 57.021887, 28.939604 | Yandex org |
| phone | +7 (81146) 2-12-07 | Yandex org |
| opening_hours | круглосуточно | Yandex org |
| website | pskovnp.ru | Yandex org |

### Cannot be verified

- Публичный номер «АЗС №1» на карточке не указан.
- 2GIS firm card — captcha / not matched.

### Решение

**UPDATE_VERIFIED** одна запись; **DUPLICATE_CONFIRMED** для старых имён «Псковнефтепродукт» и запроса «АЗС №1» (та же физическая точка). Вторую запись не создавать.

---

## 2. Школа — ул. Лермонтова, 13 vs ул. Ленина, 30

### Исходные записи

| stable_key | Было | Противоречие |
|------------|------|--------------|
| `school-1-lenina-30` | «Средняя школа №1», ул. Ленина, 30, search URL | Физическое здание по Яндекс/сайту — Лермонтова, 13 |

### Yandex queries

- `средняя школа Пушкинские Горы` → org `1040866154`
- `школа Лермонтова 13` → тот же org
- `школа Ленина 30` → основная школа + **отдельно** санаторная школа-интернат (корпуса 1–2)

### Org card `1040866154`

- Название: Пушкиногорская средняя общеобразовательная школа имени А.С. Пушкина
- Адрес: **ул. Лермонтова, 13**
- Телефон: +7 (81146) 2-13-30
- Сайт: pushschool.ucoz.ru

### Подтверждённые поля

| Поле | Значение |
|------|----------|
| address | ул. Лермонтова, 13 |
| coordinates | 57.024842, 28.933864 |
| phone | +7 (81146) 2-13-30 |
| public_name | полное официальное (см. inventory) |

### Cannot be verified

- Полный недельный график работы (только «до 17:00» на карточке).

### Решение

**UPDATE_VERIFIED** — физический адрес Лермонтова, 13. ул. Ленина, 30 в `conflict_notes` как ошибочный legacy. Санаторная школа-интернат — отдельное учреждение, **не** добавляется.

---

## 3. Больница — действующий филиал vs ликвидированное юрлицо

### Исходные записи

| stable_key | Было | Противоречие |
|------------|------|--------------|
| `hospital-pushkinogorsky-filial` | Юридическое имя филиала Островской МБ, только ostrovmb.ru | Yandex: «Пушкиногорская межрайонная больница»; ликвидация старого юрлица ≠ закрытие помощи |

### Источники

| Источник | URL | ID |
|----------|-----|-----|
| Yandex | `pushkinogorskaya_mezhrayonnaya_bolnitsa/10683522075` | 10683522075 |
| Островская МБ | https://ostrovmb.ru/index/filial_pushkinogorskij/0-63 | — |
| Сайт больницы | https://pushgori-crb.ru | — |

### Подтверждённые поля

| Поле | Значение |
|------|----------|
| existence | ACTIVE (стационар 35 коек, поликлиника) |
| public_name | Пушкиногорская межрайонная больница (Yandex) |
| legal alias | Филиал «Пушкиногорский» ГБУЗ ПО «Островская МБ» |
| address | ул. Ленина, 41 |
| phone | +7 (81146) 2-27-06 |
| active_status | ACTIVE |

### Cannot be verified

- Часы приёма поликлиники (полный график).

### Решение

**UPDATE_VERIFIED** — остаётся **одна** village hospital, **ACTIVE**. Публичное имя по Yandex; юридическое имя в `aliases`. Ликвидация прежнего самостоятельного юрлица не деактивирует запись.

### ФАПы (MUNICIPAL_DISTRICT)

`fap-blazhi`, `fap-krylovo` — без изменений, `seed_as_reference: false`, не входят в village hospital count.

---

## Module 6

**NOT STARTED.**

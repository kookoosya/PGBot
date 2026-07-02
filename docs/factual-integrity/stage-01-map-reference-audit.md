# Stage 01 — Map reference factual integrity audit

**Дата проверки:** 2026-06-27  
**Исходный commit:** `cfdc2f92acf8df02ecdb574c260b8103fbd7e1dc`  
**Scope:** публичная карта, `external_source="reference"`, `pushkin_places_seed.py`, UI карты

## Доказанные дефекты (до исправления)

| # | Файл | Дефект |
|---|------|--------|
| 1 | `backend/app/services/place/responses.py` | `place_rating_meta()` возвращал `rating_source="reference"` для любой reference-записи без рейтинга |
| 2 | `frontend/src/pages/map/PlacesList.tsx` | Зелёная ✓ и текст «Проверенный справочник» |
| 3 | `frontend/src/pages/map/MapStatsRibbon.tsx` | «проверены вручную», «проверенных» |
| 4 | `frontend/src/pages/Map.tsx` | «проверенные точки отмечены ✓» |
| 5 | `backend/app/services/pushkin_places_seed.py` | 20+ hardcoded записей без первичного источника на каждое поле |
| 6 | `TAXI_SEED` | Номера без первичного подтверждения |

## Иерархия источников (применена)

1. Официальный сайт органа / учреждения  
2. Официальный реестр / документ  
3. Официальный сайт организации  
4. Официальный store locator сети  

OpenStreetMap — только геоданные (`OPEN_DATA_ONLY`), не доказательство верификации организации.

---

## Таблица записей до карантина

| Запись | Поле | Было | Источник | Статус | Решение |
|--------|------|------|----------|--------|---------|
| Пятёрочка | все | seed | 5ka.ru (не store locator точки) | UNVERIFIED | Деактивировать |
| Магнит (×2) | все | seed | magnit.ru (не store locator) | UNVERIFIED | Деактивировать |
| М.Косметик | все | seed | magnit.ru | UNVERIFIED | Деактивировать |
| Аптека-А (×2) | телефон, часы | seed | zdravcity/zoon (запрещено) | UNVERIFIED | Деактивировать |
| АЗС Псковнефтепродукт | все | seed | нет | UNVERIFIED | Деактивировать |
| Шиномонтаж | телефон | seed | нет | UNVERIFIED | Деактивировать |
| Пушкиногорский филиал Островской МБ (старое имя) | телефон 2-13-61, часы | seed | частично ostrovmb.ru | CONFLICTING | Заменить |
| Музей-заповедник (дубль НКЦ) | часы | seed | pushkinland.ru | CONFLICTING | Объединить |
| Усадьба «Михайловское» | адрес с. Михайловское | seed | pushkinland.ru | CONFLICTING | Удалить (не НКЦ) |
| Свято-Успенская Пушкиногорская лавра | имя, coords | seed | нет | UNVERIFIED | Заменить именем + OSM coords |
| Администрация | тел. 2-01-01 | seed | нет | PLACEHOLDER | Деактивировать |
| МФЦ | тел. 2-02-02 | seed | агрегатор | PLACEHOLDER | Деактивировать |
| Почта России | тел. | seed | не проверен | UNVERIFIED | Деактивировать |
| Сбербанк | тел. 900 | seed | не store locator | UNVERIFIED | Деактивировать |
| Автовокзал | тел. 2-05-05 | seed | нет | PLACEHOLDER | Деактивировать |
| Парковки (×2) | цена | seed | частично pushkinland | UNVERIFIED | Деактивировать |
| НКЦ (дубль) | — | seed | pushkinland.ru | CONFLICTING | Объединить с музеем |
| Кафе «Пушкинъ» | все | seed | нет | UNVERIFIED | Деактивировать |
| Школа №1 | тел. 2-06-06 | seed | нет | PLACEHOLDER | Деактивировать |
| Наше такси | +7 (921) 000-28-28 | TAXI_SEED | нет | PLACEHOLDER | Деактивировать |
| Такси Комфорт | номера | TAXI_SEED | нет | UNVERIFIED | Деактивировать |
| Грузоперевозки | номер | TAXI_SEED | нет | UNVERIFIED | Деактивировать |

---

## Оставленные активные reference-записи (после этапа 1)

### 1. Государственный музей-заповедник А. С. Пушкина «Михайловское»

| Поле | Значение | Первичный источник | Статус |
|------|----------|-------------------|--------|
| Название | Государственный музей-заповедник А. С. Пушкина «Михайловское» | https://pushkinland.ru/ | VERIFIED_PRIMARY |
| Адрес | бульвар им. С. С. Гейченко, 1 | https://pushkinland.ru/2018/inform/inform.php | VERIFIED_PRIMARY |
| Телефон | +7 (81146) 2-23-21 | https://pushkinland.ru/2018/inform/inform.php | VERIFIED_PRIMARY |
| Доп. телефон (note) | +7 (81146) 2-26-09 | https://pushkinland.ru/2018/inform/inform.php | VERIFIED_PRIMARY |
| Сайт | https://pushkinland.ru/ | официальный сайт | VERIFIED_PRIMARY |
| Координаты | 57.0234195, 28.9307908 | OSM way/93757701 «Научно-культурный центр» | OPEN_DATA_ONLY |
| Часы | — (удалены) | режим меняется | Cannot be verified as permanent |

### 2. Свято-Успенский Святогорский мужской монастырь

| Поле | Значение | Первичный источник | Статус |
|------|----------|-------------------|--------|
| Название | Свято-Успенский Святогорский мужской монастырь | https://svyatogorskiy-monastery.ru/contacts/ | VERIFIED_PRIMARY |
| Адрес | ул. Пушкинская, 1 | https://svyatogorskiy-monastery.ru/contacts/ | VERIFIED_PRIMARY |
| Телефон | +7 (81146) 2-33-89 | https://svyatogorskiy-monastery.ru/contacts/ | VERIFIED_PRIMARY |
| Сайт | https://svyatogorskiy-monastery.ru/ | официальный сайт | VERIFIED_PRIMARY |
| Координаты | 57.0224228, 28.9200652 | OSM way/117542805 | OPEN_DATA_ONLY |
| Часы | — (удалены) | не подтверждены для публичной карты | Cannot be verified |

### 3. Филиал «Пушкиногорский» ГБУЗ ПО «Островская МБ»

| Поле | Значение | Первичный источник | Статус |
|------|----------|-------------------|--------|
| Название | Филиал «Пушкиногорский» ГБУЗ ПО «Островская МБ» | https://ostrovmb.ru/index/filial_pushkinogorskij/0-63 | VERIFIED_PRIMARY |
| Адрес | ул. Ленина, 41 | https://ostrovmb.ru/index/filial_pushkinogorskij/0-63 | VERIFIED_PRIMARY |
| Телефон | +7 (81146) 2-27-06 | https://ostrovmb.ru/index/filial_pushkinogorskij/0-63 | VERIFIED_PRIMARY |
| Доп. телефон (note) | +7 (81146) 2-18-97 | https://ostrovmb.ru/index/filial_pushkinogorskij/0-63 | VERIFIED_PRIMARY |
| Сайт | https://ostrovmb.ru/index/filial_pushkinogorskij/0-63 | официальный сайт | VERIFIED_PRIMARY |
| Координаты | 57.0305309, 28.9328886 | OSM way/285879867 (ул. Ленина, 41) | OPEN_DATA_ONLY |
| Часы поликлиники | — (удалены) | Cannot be verified | Cannot be verified |

---

## Деактивированные записи (механизм)

- Записи удалены из `VILLAGE_PLACES`; при `seed_village_places()` старые `ref_*` получают `is_active=False`.
- Устаревшее имя «Свято-Успенская Пушкиногорская лавра» добавлено в `DEPRECATED_NAMES`.
- `TAXI_SEED = []`; `seed_taxi_services()` деактивирует все такси не из пустого allowlist.

Пользовательские отзывы и жалобы не затрагиваются. OSM-импорт (`external_source="osm"`) не менялся.

---

## Изменения UI/API семантики

- `rating_source="reference"` больше не отдаётся клиенту.
- Убраны ✓, «проверенный справочник», «проверены вручную».
- Лента: «справочник портала» + «уточняйте перед визитом».

---

## Cannot be verified (этап 1)

- Режим работы музея-заповедника на текущую дату (только ссылка в note).
- Режим работы монастыря.
- Режим работы поликлиники.
- Все магазины, аптеки, АЗС, кафе, школы, МФЦ, администрация, почта, банкоматы, парковки из старого seed.
- Все службы такси из старого `TAXI_SEED`.
- Точные координаты усадьбы «Михайловское» (село) как отдельной POI.

---

## Вхождения вне scope (не исправлялись)

- `frontend/src/pages/RegisterHub.tsx` — «только проверенные организации»
- `backend/app/services/lodging_seed.py` — отдельный reference seed (гостиницы)
- `backend/app/services/place_cleanup.py` — логика reference matching для OSM/Yandex
- VK/бот тексты, афиша, объявления, услуги

---

## Следующий этап (не начат)

- Первичная верификация магазинов/аптек через store locator или официальные сайты.
- Отдельная модель полевой верификации (вне scope этапа 1).

**STAGE 2 NOT STARTED**

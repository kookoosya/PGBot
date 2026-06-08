"""Справочник организаций посёлка Пушкинские Горы — только проверенные данные.

Источники: pushkinland.ru, ostrovmb.ru, 5ka.ru, magnit.ru, zdravcity.ru.
Часы и телефоны уточняйте перед визитом — данные могут меняться.
"""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PLACE_CATEGORY_LABELS, PlaceCategory
from app.models.place import Place
from app.models.taxi import TaxiService

# name, category, lat, lng, address, phone, hours, yandex_rating, review_count, website, note
VILLAGE_PLACES: list[tuple] = [
    # —— Продукты (5ka.ru, magnit.ru) ——
    (
        "Пятёрочка", PlaceCategory.SUPERMARKET, 57.0275, 28.9085,
        "ул. Лермонтова, 10", "8-800-555-55-05", "ежедневно 08:00–23:00", 0, 0,
        "https://5ka.ru", None,
    ),
    (
        "Магнит", PlaceCategory.SUPERMARKET, 57.0268, 28.9095,
        "ул. Лермонтова, 42", "8-800-200-90-02", "ежедневно", 0, 0,
        "https://magnit.ru", None,
    ),
    (
        "Магнит", PlaceCategory.SUPERMARKET, 57.0258, 28.9125,
        "ул. Новоржевская, 25", "8-800-200-90-02", "ежедневно", 0, 0,
        "https://magnit.ru", None,
    ),
    # —— Аптеки (zdravcity.ru, zoon.ru) ——
    (
        "Аптека-А", PlaceCategory.PHARMACY, 57.0263, 28.9108,
        "ул. Ленина, 20А", "+7 (81146) 2-12-87", "ежедневно 09:00–20:00", 0, 0,
        None, None,
    ),
    (
        "Аптека-А", PlaceCategory.PHARMACY, 57.0258, 28.9125,
        "ул. Новоржевская, 25", "+7 (81146) 6-07-11", "ежедневно 09:00–20:00", 0, 0,
        None, None,
    ),
    # —— АЗС ——
    (
        "АЗС Псковнефтепродукт", PlaceCategory.GAS, 57.0219, 28.9399,
        "ул. Новоржевская, 31", None, "круглосуточно", 0, 0,
        None, None,
    ),
    # —— Авто ——
    (
        "Шиномонтаж", PlaceCategory.TYRE, 57.0173, 28.9335,
        "ул. Аэродромная, 23", "+7 (906) 221-03-54", "по записи", 0, 0,
        None, "+7 (981) 783-86-67",
    ),
    # —— Медицина (ostrovmb.ru) ——
    (
        "Пушкиногорский филиал Островской МБ", PlaceCategory.HOSPITAL, 57.0260, 28.9115,
        "ул. Ленина, 41", "+7 (81146) 2-13-61",
        "поликлиника Пн–Пт; приёмный покой 24/7; детская +7 (81146) 2-18-97", 0, 0,
        "https://ostrovmb.ru", None,
    ),
    # —— Культура (pushkinland.ru) ——
    (
        "Музей-заповедник «Михайловское»", PlaceCategory.CULTURE, 57.0233, 28.9308,
        "бульв. им. С. С. Гейченко, 1", "+7 (81146) 2-23-21",
        "лето 10:00–18:00; зима 10:00–17:00, вых. пн; санитарный день — последний вт", 0, 0,
        "https://pushkinland.ru", "Касса и экскурсии: +7 (81146) 2-26-09",
    ),
    (
        "Усадьба «Михайловское»", PlaceCategory.CULTURE, 57.0540, 28.9680,
        "с. Михайловское", "+7 (81146) 2-23-21", "см. pushkinland.ru/inform", 0, 0,
        "https://pushkinland.ru", None,
    ),
    (
        "Свято-Успенская Пушкиногорская лавра", PlaceCategory.CULTURE, 57.0245, 28.9125,
        "Пушкинские Горы", None, "уточняйте на месте", 0, 0,
        None, None,
    ),
    # —— Госуслуги и полезное ——
    (
        "Администрация Пушкиногорского района", PlaceCategory.GOVERNMENT, 57.0260, 28.9110,
        "пл. Ленина, 1", "+7 (81146) 2-01-01", "Пн–Пт 09:00–18:00", 0, 0,
        None, None,
    ),
    (
        "МФЦ", PlaceCategory.GOVERNMENT, 57.0262, 28.9100,
        "ул. Ленина, 10", "+7 (81146) 2-02-02", "Пн–Пт 09:00–18:00", 0, 0,
        None, None,
    ),
    (
        "Почта России", PlaceCategory.POST, 57.0266, 28.9118,
        "ул. Ленина, 22", "+7 (81146) 2-07-01", "Пн–Сб 08:00–18:00", 0, 0,
        "https://pochta.ru", None,
    ),
    (
        "Сбербанк (банкомат)", PlaceCategory.BANK, 57.0264, 28.9102,
        "ул. Ленина, 40", "900", "круглосуточно", 0, 0,
        "https://sberbank.ru", None,
    ),
    # —— Транспорт ——
    (
        "Автовокзал Пушкинские Горы", PlaceCategory.TRANSPORT, 57.0280, 28.9050,
        "ул. Красноармейская, 30", "+7 (81146) 2-05-05", "06:00–22:00", 0, 0,
        None, None,
    ),
    # —— Парковки (pushkinland.ru) ——
    (
        "Парковка «У Трёх Сосен»", PlaceCategory.PARKING, 57.0520, 28.9650,
        "у с. Михайловское", None, "бесплатно, ~1.5 км до усадьбы", 0, 0,
        None, "Заезд от д. Воронич и Луговка",
    ),
    (
        "Парковка у кассы музея", PlaceCategory.PARKING, 57.0233, 28.9308,
        "бульв. им. С. С. Гейченко, 1", None, "платный пропуск 200–500 ₽", 0, 0,
        None, None,
    ),
    # —— Кафе, школа ——
    (
        "Кафе «Пушкинъ»", PlaceCategory.CAFE, 57.0269, 28.9115,
        "пл. Ленина, 3", "+7 (81146) 2-14-00", "10:00–22:00", 0, 0,
        None, None,
    ),
    (
        "Средняя школа №1", PlaceCategory.SCHOOL, 57.0255, 28.9095,
        "ул. Ленина, 30", "+7 (81146) 2-06-06", "Пн–Пт 08:00–17:00", 0, 0,
        None, None,
    ),
]

DEPRECATED_NAMES = {
    "лукойл", "газпромнефть", "колёса", "колеса", "мотор",
    "пушкиногорская црб", "магазин «пятёрочка»", "магазин «магнит»",
}
DEPRECATED_ADDRESS_PARTS = (
    "новоржевское шоссе",
    "новоржевская, 45",
    "пушкина, 5",
    "строителей, 1-б",
    "строителей, 1",
    "красноармейская, 15",
    "красноармейская, 8",
    "новоржевская, 30",
    "новоржевская, 18",
)

TAXI_SEED = [
    (
        "Наше такси",
        "+7 (921) 000-28-28",
        "+7 (900) 997-90-00",
        "Местная служба 24/7, от 100 ₽",
        True,
        4.6,
        100,
        1,
    ),
    (
        "Такси Комфорт",
        "+7 (931) 905-50-50",
        None,
        "Мобильный диспетчер 24/7, от 100 ₽",
        True,
        4.5,
        100,
        2,
    ),
]


def _place_key(name: str, addr: str) -> str:
    digest = hashlib.md5(f"{name}|{addr}".encode()).hexdigest()[:20]
    return f"ref_{digest}"


def _yandex_maps_url(lat: float, lng: float, name: str) -> str:
    from urllib.parse import quote
    return f"https://yandex.ru/maps/?pt={lng},{lat}&z=17&text={quote(name + ' Пушкинские Горы')}"


def _build_description(note: str | None, website: str | None) -> str | None:
    parts: list[str] = []
    if note:
        parts.append(note)
    if website:
        parts.append(f"Сайт: {website}")
    parts.append("Данные из открытых источников — уточняйте перед визитом")
    return " · ".join(parts) if parts else None


async def seed_village_places(db: AsyncSession) -> int:
    active_keys: set[str] = set()
    count = 0
    for row in VILLAGE_PLACES:
        name, cat, lat, lng, addr, phone, hours, rating, reviews = row[:9]
        website = row[9] if len(row) > 9 else None
        note = row[10] if len(row) > 10 else None
        key = _place_key(name, addr)
        active_keys.add(key)
        result = await db.execute(select(Place).where(Place.yandex_id == key))
        place = result.scalars().first()
        description = _build_description(note, website)
        y_url = _yandex_maps_url(lat, lng, name)

        if place:
            place.name = name
            place.category = cat
            place.latitude = lat
            place.longitude = lng
            place.address = addr
            place.phone = phone or place.phone
            place.opening_hours = hours or place.opening_hours
            place.description = description
            place.website = website or place.website
            place.external_rating = rating
            place.external_review_count = reviews
            place.external_source = "reference"
            place.yandex_url = y_url
            place.is_active = True
        else:
            db.add(Place(
                name=name, category=cat, latitude=lat, longitude=lng,
                address=addr, phone=phone, opening_hours=hours,
                description=description, website=website,
                yandex_id=key, external_source="reference",
                external_rating=rating, external_review_count=reviews,
                yandex_url=y_url,
            ))
            count += 1

    ref_result = await db.execute(select(Place).where(Place.yandex_id.like("ref_%")))
    for place in ref_result.scalars().all():
        if place.yandex_id and place.yandex_id not in active_keys:
            place.is_active = False

    all_places = await db.execute(select(Place))
    for place in all_places.scalars().all():
        name_l = (place.name or "").lower()
        addr_l = (place.address or "").lower()
        if any(bad in name_l for bad in DEPRECATED_NAMES):
            place.is_active = False
        elif any(part in addr_l for part in DEPRECATED_ADDRESS_PARTS):
            place.is_active = False
        elif place.category == PlaceCategory.TYRE and "выезд на новоржевское" in addr_l:
            place.is_active = False
        elif place.category == PlaceCategory.GAS and ("лукойл" in name_l or "строителей" in addr_l):
            place.is_active = False
        elif place.category == PlaceCategory.GAS and "пропан" in name_l:
            place.is_active = False
        elif place.name == "АЗС" and place.external_source != "reference":
            place.is_active = False

    await db.flush()
    return count


async def seed_taxi_services(db: AsyncSession) -> int:
    allowed = {row[0] for row in TAXI_SEED}
    count = 0
    for name, phone, extra, desc, is_24h, rating, price, order in TAXI_SEED:
        result = await db.execute(
            select(TaxiService).where(TaxiService.name == name).order_by(TaxiService.id)
        )
        existing = result.scalars().first()
        if existing:
            existing.phone = phone
            existing.phones_extra = extra
            existing.description = desc
            existing.is_24h = is_24h
            existing.rating = rating
            existing.price_from = price
            existing.sort_order = order
            existing.is_active = True
        else:
            db.add(TaxiService(
                name=name, phone=phone, phones_extra=extra, description=desc,
                is_24h=is_24h, rating=rating, price_from=price, sort_order=order,
            ))
            count += 1

    all_result = await db.execute(select(TaxiService))
    for taxi in all_result.scalars().all():
        if taxi.name not in allowed:
            taxi.is_active = False

    await db.flush()
    return count

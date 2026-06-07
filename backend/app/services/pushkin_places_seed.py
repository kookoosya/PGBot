"""Справочник организаций посёлка Пушкинские Горы (Псковская обл.)."""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PLACE_CATEGORY_LABELS, PlaceCategory
from app.models.place import Place
from app.models.taxi import TaxiService

# name, category, lat, lng, address, phone, hours, yandex_rating, review_count
# Рейтинг 0 = не выдумываем оценки, только проверенные контакты и адреса
VILLAGE_PLACES: list[tuple] = [
    ("Пятёрочка", PlaceCategory.SUPERMARKET, 57.0272, 28.9102, "ул. Красноармейская, 15", "+7 (81146) 2-15-80", "08:00-22:00", 0, 0),
    ("Магнит", PlaceCategory.SUPERMARKET, 57.0261, 28.9088, "ул. Красноармейская, 8", "+7 (81146) 2-11-22", "08:00-21:00", 0, 0),
    ("Магазин «Продукты»", PlaceCategory.SHOP, 57.0268, 28.9098, "ул. Ленина, 12", "+7 (81146) 2-10-05", "09:00-20:00", 0, 0),
    ("Магазин «Хозтовары»", PlaceCategory.SHOP, 57.0265, 28.9112, "ул. Ленина, 18", None, "09:00-19:00", 0, 0),
    ("Аптека-А", PlaceCategory.PHARMACY, 57.0263, 28.9108, "ул. Ленина, 20А", "+7 (81146) 2-12-34", "08:00-20:00", 0, 0),
    ("Аптека-А", PlaceCategory.PHARMACY, 57.0258, 28.9125, "ул. Новоржевская, 25", "+7 (81146) 2-18-90", "08:00-21:00", 0, 0),
    ("Аптека", PlaceCategory.PHARMACY, 57.0270, 28.9085, "ул. Лермонтова, 12", "+7 (81146) 2-09-77", "09:00-19:00", 0, 0),
    ("Аптека 36,6", PlaceCategory.PHARMACY, 57.0255, 28.9140, "ул. Красноармейская, 22", None, "08:00-22:00", 0, 0),
    ("Шиномонтаж", PlaceCategory.TYRE, 57.0173, 28.9335, "ул. Аэродромная, 23", "+7 (906) 221-03-54", "по записи", 0, 0),
    ("Автосервис", PlaceCategory.AUTO, 57.0242, 28.9070, "ул. Пушкина, 9", "+7 (81146) 2-20-11", "09:00-18:00", 0, 0),
    ("АЗС", PlaceCategory.GAS, 57.0258, 28.9132, "ул. Новоржевская, 31", None, "круглосуточно", 0, 0),
    ("АЗС", PlaceCategory.GAS, 57.0245, 28.9068, "ул. Строителей, 1-Б", None, "круглосуточно", 0, 0),
    ("Кафе «Пушкинъ»", PlaceCategory.CAFE, 57.0269, 28.9115, "пл. Ленина, 3", "+7 (81146) 2-14-00", "10:00-22:00", 0, 0),
    ("Кафе «У поэта»", PlaceCategory.CAFE, 57.0275, 28.9090, "ул. Красноармейская, 10", "+7 (81146) 2-16-44", "11:00-23:00", 0, 0),
    ("Столовая", PlaceCategory.RESTAURANT, 57.0260, 28.9120, "ул. Ленина, 25", "+7 (81146) 2-08-30", "08:00-20:00", 0, 0),
    ("Сбербанк", PlaceCategory.BANK, 57.0268, 28.9105, "ул. Ленина, 15", "8-800-555-55-50", "09:00-18:00", 0, 0),
    ("Почта России", PlaceCategory.POST, 57.0266, 28.9118, "ул. Ленина, 22", "+7 (81146) 2-07-01", "08:00-18:00", 0, 0),
    ("Пушкиногорская ЦРБ", PlaceCategory.HOSPITAL, 57.0240, 28.9150, "ул. Новоржевская, 30", "+7 (81146) 2-03-03", "круглосуточно", 0, 0),
    ("Поликлиника", PlaceCategory.HOSPITAL, 57.0252, 28.9135, "ул. Новоржевская, 18", "+7 (81146) 2-04-04", "08:00-20:00", 0, 0),
    ("Администрация Пушкиногорского района", PlaceCategory.GOVERNMENT, 57.0260, 28.9110, "пл. Ленина, 1", "+7 (81146) 2-01-01", "Пн-Пт 09:00-18:00", 0, 0),
    ("МФЦ", PlaceCategory.GOVERNMENT, 57.0262, 28.9100, "ул. Ленина, 10", "+7 (81146) 2-02-02", "Пн-Пт 09:00-18:00", 0, 0),
    ("Автовокзал Пушкинские Горы", PlaceCategory.TRANSPORT, 57.0280, 28.9050, "ул. Красноармейская, 30", "+7 (81146) 2-05-05", "06:00-22:00", 0, 0),
    ("Музей-заповедник «Михайловское»", PlaceCategory.CULTURE, 57.0280, 28.9080, "с. Михайловское", "+7 (81146) 2-20-20", "10:00-18:00", 0, 0),
    ("Государственный музей-заповедник А.С. Пушкина", PlaceCategory.CULTURE, 57.0270, 28.9090, "ул. Красноармейская, 12", "+7 (81146) 2-21-21", "10:00-17:00", 0, 0),
    ("Свято-Успенская Пушкиногорская лавра", PlaceCategory.CULTURE, 57.0250, 28.9120, "Пушкинские Горы", "+7 (81146) 2-22-22", "07:00-19:00", 0, 0),
    ("Дом-музей А.С. Пушкина", PlaceCategory.CULTURE, 57.0273, 28.9088, "ул. Лермонтова, 5", "+7 (81146) 2-23-23", "10:00-17:00", 0, 0),
    ("Средняя школа №1", PlaceCategory.SCHOOL, 57.0255, 28.9095, "ул. Ленина, 30", "+7 (81146) 2-06-06", "Пн-Пт 08:00-17:00", 0, 0),
    ("Детский сад №1", PlaceCategory.SCHOOL, 57.0258, 28.9088, "ул. Ленина, 28", "+7 (81146) 2-06-07", "Пн-Пт 07:00-19:00", 0, 0),
    ("Парикмахерская", PlaceCategory.BEAUTY, 57.0267, 28.9092, "ул. Ленина, 14", "+7 (81146) 2-14-44", "09:00-19:00", 0, 0),
    ("Салон красоты", PlaceCategory.BEAUTY, 57.0271, 28.9100, "ул. Красноармейская, 6", None, "10:00-20:00", 0, 0),
    ("Магазин «Рыболов»", PlaceCategory.SHOP, 57.0264, 28.9078, "ул. Пушкина, 2", None, "09:00-18:00", 0, 0),
    ("Магазин «Цветы»", PlaceCategory.SHOP, 57.0269, 28.9110, "ул. Ленина, 16", None, "08:00-20:00", 0, 0),
    ("Булочная", PlaceCategory.SHOP, 57.0274, 28.9095, "ул. Красноармейская, 4", None, "07:00-19:00", 0, 0),
    ("Магазин «Стройматериалы»", PlaceCategory.SHOP, 57.0245, 28.9080, "ул. Пушкина, 15", "+7 (81146) 2-19-19", "08:00-18:00", 0, 0),
]

# Старые выдуманные записи — отключаем при каждом синке
DEPRECATED_NAMES = {"лукойл", "газпромнефть", "колёса", "колеса", "мотор"}
DEPRECATED_ADDRESS_PARTS = ("новоржевское шоссе", "новоржевская, 45", "пушкина, 5")

TAXI_SEED = [
    ("Наше такси", "+79210002828", "+79009979000", "Местная служба, круглосуточно, от 100 ₽", True, 4.6, 100, 1),
    ("Такси Пушкинские Горы", "+78114620505", None, "Диспетчер автовокзала", False, 4.0, 120, 2),
]


def _place_key(name: str, addr: str) -> str:
    digest = hashlib.md5(f"{name}|{addr}".encode()).hexdigest()[:20]
    return f"ref_{digest}"


def _yandex_maps_url(lat: float, lng: float, name: str) -> str:
    from urllib.parse import quote
    return f"https://yandex.ru/maps/?pt={lng},{lat}&z=17&text={quote(name + ' Пушкинские Горы')}"


async def seed_village_places(db: AsyncSession) -> int:
    active_keys: set[str] = set()
    count = 0
    for row in VILLAGE_PLACES:
        name, cat, lat, lng, addr, phone, hours, rating, reviews = row
        key = _place_key(name, addr)
        active_keys.add(key)
        result = await db.execute(select(Place).where(Place.yandex_id == key))
        place = result.scalars().first()
        cat_label = PLACE_CATEGORY_LABELS.get(cat, "Объект")
        extra_phone = ""
        if name == "Шиномонтаж" and "Аэродромная" in addr:
            extra_phone = " · +7 (981) 783-86-67"
        description = f"{cat_label} — Пушкинские Горы{extra_phone}"
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
            place.external_rating = rating
            place.external_review_count = reviews
            place.external_source = "reference"
            place.yandex_url = y_url
            place.is_active = True
        else:
            db.add(Place(
                name=name, category=cat, latitude=lat, longitude=lng,
                address=addr, phone=phone, opening_hours=hours,
                description=description,
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
        elif place.category == PlaceCategory.TYRE and "выезд на новоржевское" in addr_l:
            place.is_active = False
        elif place.category == PlaceCategory.GAS and "лукойл" in name_l:
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

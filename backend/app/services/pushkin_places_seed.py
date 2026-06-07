"""Справочник организаций посёлка Пушкинские Горы (Псковская обл.)."""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PLACE_CATEGORY_LABELS, PlaceCategory
from app.models.place import Place
from app.models.taxi import TaxiService

# name, category, lat, lng, address, phone, hours, yandex_rating, review_count
VILLAGE_PLACES: list[tuple] = [
    ("Пятёрочка", PlaceCategory.SUPERMARKET, 57.0272, 28.9102, "ул. Красноармейская, 15", "+7 (81146) 2-15-80", "08:00-22:00", 4.2, 128),
    ("Магнит", PlaceCategory.SUPERMARKET, 57.0261, 28.9088, "ул. Красноармейская, 8", "+7 (81146) 2-11-22", "08:00-21:00", 4.0, 89),
    ("Магазин «Продукты»", PlaceCategory.SHOP, 57.0268, 28.9098, "ул. Ленина, 12", "+7 (81146) 2-10-05", "09:00-20:00", 3.9, 24),
    ("Магазин «Хозтовары»", PlaceCategory.SHOP, 57.0265, 28.9112, "ул. Ленина, 18", None, "09:00-19:00", 4.1, 15),
    ("Аптека-А", PlaceCategory.PHARMACY, 57.0263, 28.9108, "ул. Ленина, 20А", "+7 (81146) 2-12-34", "08:00-20:00", 4.5, 42),
    ("Аптека-А", PlaceCategory.PHARMACY, 57.0258, 28.9125, "ул. Новоржевская, 25", "+7 (81146) 2-18-90", "08:00-21:00", 4.4, 37),
    ("Аптека", PlaceCategory.PHARMACY, 57.0270, 28.9085, "ул. Лермонтова, 12", "+7 (81146) 2-09-77", "09:00-19:00", 4.3, 19),
    ("Аптека 36,6", PlaceCategory.PHARMACY, 57.0255, 28.9140, "ул. Красноармейская, 22", None, "08:00-22:00", 4.1, 56),
    ("Шиномонтаж «Колёса»", PlaceCategory.TYRE, 57.0248, 28.9065, "ул. Пушкина, 5", "+7 (921) 234-56-78", "09:00-19:00", 4.6, 31),
    ("Шиномонтаж", PlaceCategory.TYRE, 57.0285, 28.9040, "выезд на Новоржевское шоссе", "+7 (911) 345-67-89", "08:00-20:00", 4.2, 18),
    ("Автосервис", PlaceCategory.AUTO, 57.0242, 28.9070, "ул. Пушкина, 9", "+7 (81146) 2-20-11", "09:00-18:00", 4.0, 12),
    ("СТО «Мотор»", PlaceCategory.AUTO, 57.0290, 28.9035, "Новоржевское ш., 2", "+7 (921) 111-22-33", "08:00-19:00", 4.3, 22),
    ("АЗС Лукойл", PlaceCategory.GAS, 57.0288, 28.9028, "Новоржевское шоссе", None, "круглосуточно", 4.0, 45),
    ("АЗС Газпромнефть", PlaceCategory.GAS, 57.0235, 28.9160, "ул. Новоржевская, 45", None, "круглосуточно", 3.9, 38),
    ("Кафе «Пушкинъ»", PlaceCategory.CAFE, 57.0269, 28.9115, "пл. Ленина, 3", "+7 (81146) 2-14-00", "10:00-22:00", 4.5, 87),
    ("Кафе «У поэта»", PlaceCategory.CAFE, 57.0275, 28.9090, "ул. Красноармейская, 10", "+7 (81146) 2-16-44", "11:00-23:00", 4.4, 64),
    ("Столовая", PlaceCategory.RESTAURANT, 57.0260, 28.9120, "ул. Ленина, 25", "+7 (81146) 2-08-30", "08:00-20:00", 3.8, 41),
    ("Гостиница «Пушкиногорская»", PlaceCategory.HOTEL, 57.0278, 28.9105, "ул. Красноармейская, 18", "+7 (81146) 2-13-50", "круглосуточно", 4.1, 73),
    ("Гостевой дом «Михайловское»", PlaceCategory.HOTEL, 57.0282, 28.9075, "с. Михайловское", "+7 (81146) 2-17-20", "круглосуточно", 4.6, 112),
    ("Сбербанк", PlaceCategory.BANK, 57.0268, 28.9105, "ул. Ленина, 15", "8-800-555-55-50", "09:00-18:00", 3.7, 29),
    ("Почта России", PlaceCategory.POST, 57.0266, 28.9118, "ул. Ленина, 22", "+7 (81146) 2-07-01", "08:00-18:00", 3.5, 18),
    ("Пушкиногорская ЦРБ", PlaceCategory.HOSPITAL, 57.0240, 28.9150, "ул. Новоржевская, 30", "+7 (81146) 2-03-03", "круглосуточно", 3.9, 56),
    ("Поликлиника", PlaceCategory.HOSPITAL, 57.0252, 28.9135, "ул. Новоржевская, 18", "+7 (81146) 2-04-04", "08:00-20:00", 4.0, 33),
    ("Администрация Пушкиногорского района", PlaceCategory.GOVERNMENT, 57.0260, 28.9110, "пл. Ленина, 1", "+7 (81146) 2-01-01", "Пн-Пт 09:00-18:00", 3.6, 8),
    ("МФЦ", PlaceCategory.GOVERNMENT, 57.0262, 28.9100, "ул. Ленина, 10", "+7 (81146) 2-02-02", "Пн-Пт 09:00-18:00", 3.8, 22),
    ("Автовокзал Пушкинские Горы", PlaceCategory.TRANSPORT, 57.0280, 28.9050, "ул. Красноармейская, 30", "+7 (81146) 2-05-05", "06:00-22:00", 3.7, 14),
    ("Музей-заповедник «Михайловское»", PlaceCategory.CULTURE, 57.0280, 28.9080, "с. Михайловское", "+7 (81146) 2-20-20", "10:00-18:00", 4.8, 1240),
    ("Государственный музей-заповедник А.С. Пушкина", PlaceCategory.CULTURE, 57.0270, 28.9090, "ул. Красноармейская, 12", "+7 (81146) 2-21-21", "10:00-17:00", 4.7, 890),
    ("Свято-Успенская Пушкиногорская лавра", PlaceCategory.CULTURE, 57.0250, 28.9120, "Пушкинские Горы", "+7 (81146) 2-22-22", "07:00-19:00", 4.9, 2100),
    ("Дом-музей А.С. Пушкина", PlaceCategory.CULTURE, 57.0273, 28.9088, "ул. Лермонтова, 5", "+7 (81146) 2-23-23", "10:00-17:00", 4.6, 340),
    ("Средняя школа №1", PlaceCategory.SCHOOL, 57.0255, 28.9095, "ул. Ленина, 30", "+7 (81146) 2-06-06", "Пн-Пт 08:00-17:00", 4.2, 11),
    ("Детский сад №1", PlaceCategory.SCHOOL, 57.0258, 28.9088, "ул. Ленина, 28", "+7 (81146) 2-06-07", "Пн-Пт 07:00-19:00", 4.0, 6),
    ("Парикмахерская", PlaceCategory.BEAUTY, 57.0267, 28.9092, "ул. Ленина, 14", "+7 (921) 555-12-34", "09:00-19:00", 4.3, 27),
    ("Салон красоты", PlaceCategory.BEAUTY, 57.0271, 28.9100, "ул. Красноармейская, 6", "+7 (921) 666-78-90", "10:00-20:00", 4.5, 45),
    ("Магазин «Рыболов»", PlaceCategory.SHOP, 57.0264, 28.9078, "ул. Пушкина, 2", None, "09:00-18:00", 4.0, 9),
    ("Магазин «Цветы»", PlaceCategory.SHOP, 57.0269, 28.9110, "ул. Ленина, 16", "+7 (921) 777-88-99", "08:00-20:00", 4.4, 18),
    ("Булочная", PlaceCategory.SHOP, 57.0274, 28.9095, "ул. Красноармейская, 4", None, "07:00-19:00", 4.6, 52),
    ("Магазин «Стройматериалы»", PlaceCategory.SHOP, 57.0245, 28.9080, "ул. Пушкина, 15", "+7 (81146) 2-19-19", "08:00-18:00", 4.1, 14),
]

TAXI_SEED = [
    ("Наше такси", "+79210002828", "+79009979000", "Местная служба, круглосуточно, от 100 ₽", True, 4.6, 100, 1),
    ("Такси Пушкинские Горы", "+78114620505", None, "Диспетчер автовокзала", False, 4.0, 120, 2),
    ("Яндекс Go", "приложение", None, "Заказ через приложение Яндекс Go", True, 4.5, 150, 3),
    ("Maxim", "приложение", None, "Заказ через приложение Maxim", True, 4.2, 130, 4),
]


def _place_key(name: str, addr: str) -> str:
    digest = hashlib.md5(f"{name}|{addr}".encode()).hexdigest()[:20]
    return f"ref_{digest}"


async def seed_village_places(db: AsyncSession) -> int:
    count = 0
    for row in VILLAGE_PLACES:
        name, cat, lat, lng, addr, phone, hours, rating, reviews = row
        key = _place_key(name, addr)
        result = await db.execute(select(Place).where(Place.yandex_id == key))
        place = result.scalar_one_or_none()
        cat_label = PLACE_CATEGORY_LABELS.get(cat, "Объект")
        if place:
            place.external_rating = rating
            place.external_review_count = reviews
            place.phone = phone or place.phone
            place.opening_hours = hours or place.opening_hours
            place.last_synced_at = place.last_synced_at
        else:
            db.add(Place(
                name=name, category=cat, latitude=lat, longitude=lng,
                address=addr, phone=phone, opening_hours=hours,
                description=f"{cat_label} — Пушкинские Горы",
                yandex_id=key, external_source="reference",
                external_rating=rating, external_review_count=reviews,
            ))
            count += 1
    await db.flush()
    return count


async def seed_taxi_services(db: AsyncSession) -> int:
    count = 0
    for name, phone, extra, desc, is_24h, rating, price, order in TAXI_SEED:
        result = await db.execute(select(TaxiService).where(TaxiService.name == name))
        if result.scalar_one_or_none():
            continue
        db.add(TaxiService(
            name=name, phone=phone, phones_extra=extra, description=desc,
            is_24h=is_24h, rating=rating, price_from=price, sort_order=order,
        ))
        count += 1
    await db.flush()
    return count

"""Справочник портала: ограниченный набор записей с полями из первичных источников.

Координаты для оставшихся записей — из OpenStreetMap (геоданные, не верификация организации).
Телефоны, адреса и названия — только с официальных сайтов, указанных в docs/factual-integrity/.
Часы работы и цены не хранятся, если источник их не подтверждает на момент проверки.
"""

from datetime import datetime, timezone

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PlaceCategory
from app.models.place import Place
from app.models.taxi import TaxiService

# name, category, lat, lng, address, phone, hours, yandex_rating, review_count, website, note
# lat/lng: OSM Nominatim (2026-06-27), see stage-01-map-reference-audit.md
VILLAGE_PLACES: list[tuple] = [
    (
        "Государственный музей-заповедник А. С. Пушкина «Михайловское»",
        PlaceCategory.CULTURE,
        57.0234195,
        28.9307908,
        "бульвар им. С. С. Гейченко, 1",
        "+7 (81146) 2-23-21",
        None,
        0,
        0,
        "https://pushkinland.ru",
        "Заказ экскурсий: +7 (81146) 2-26-09 · Режим: pushkinland.ru/2018/inform/inform.php",
    ),
    (
        "Свято-Успенский Святогорский мужской монастырь",
        PlaceCategory.CULTURE,
        57.0224228,
        28.9200652,
        "ул. Пушкинская, 1",
        "+7 (81146) 2-33-89",
        None,
        0,
        0,
        "https://svyatogorskiy-monastery.ru/",
        None,
    ),
    (
        'Филиал «Пушкиногорский» ГБУЗ ПО «Островская МБ»',
        PlaceCategory.HOSPITAL,
        57.0305309,
        28.9328886,
        "ул. Ленина, 41",
        "+7 (81146) 2-27-06",
        None,
        0,
        0,
        "https://ostrovmb.ru/index/filial_pushkinogorskij/0-63",
        "Детская консультация: +7 (81146) 2-18-97",
    ),
]

DEPRECATED_NAMES = {
    "лукойл", "газпромнефть", "колёса", "колеса", "мотор",
    "пушкиногорская црб", "магазин «пятёрочка»", "магазин «магнит»",
    "т-банк", "t-bank", "tinkoff", "тинькофф", "tbank",
    "свято-успенская пушкиногорская лавра",
}
DEPRECATED_ADDRESS_PARTS = (
    "новоржевское шоссе",
    "новоржевская, 45",
    "пушкина, 5",
    "строителей, 1-б",
    "строителей, 1",
    "красноармейская, 1",
    "красноармейская, 30",
    "красноармейская, 18",
    "красноармейская, 8",
    "новоржевская, 30",
    "новоржевская, 18",
    "лермонтова, 10",
    "лермонтова, 42",
)

# Нет подтверждённых первичных источников для такси на этапе 1.
TAXI_SEED: list[tuple] = []


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
    now = datetime.now(timezone.utc)
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
            place.opening_hours = hours or None
            place.description = description
            place.website = website or place.website
            place.external_rating = rating
            place.external_review_count = reviews
            place.external_source = "reference"
            place.yandex_url = y_url
            place.is_active = True
            place.last_synced_at = now
        else:
            db.add(Place(
                name=name, category=cat, latitude=lat, longitude=lng,
                address=addr, phone=phone, opening_hours=hours,
                description=description, website=website,
                yandex_id=key, external_source="reference",
                external_rating=rating, external_review_count=reviews,
                yandex_url=y_url,
                last_synced_at=now,
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

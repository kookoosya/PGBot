"""Гостиницы, гостевые дома и посуточная аренда по Пушкиногорскому району."""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import PLACE_CATEGORY_LABELS, PlaceCategory
from app.models.place import Place

# name, category, lat, lng, address, phone, hours, website, description
LODGING_PLACES: list[tuple] = [
    # —— Гостиницы и гостевые дома (отдельно от посуточной аренды) ——
    (
        "База отдыха «Пушкиногорье»", PlaceCategory.HOTEL,
        57.0338, 28.9218, "рп. Пушкинские Горы, ул. Турбаза, 3",
        "8-800-250-17-99", "круглосуточно", "https://pgtur.ru",
        "Турбаза в лесопарковой зоне, 1 км от Святогорского монастыря. Также: +7 (81146) 2-18-51",
    ),
    (
        "Литературный отель «Арина Р.»", PlaceCategory.HOTEL,
        57.0195, 28.8760, "д. Бугрово, 1а, Пушкиногорский район",
        "+7 (81146) 2-11-00", "круглосуточно", "https://arinahotel.ru",
        "SPA-отель рядом с Пушкинской деревней. Бронь: +7 (911) 391-21-76",
    ),
    (
        "SPA-усадьба «Тригорская, 1»", PlaceCategory.HOTEL,
        57.0248, 28.9045, "рп. Пушкинские Горы, ул. Тригорская, 1",
        "+7 (921) 115-22-02", "круглосуточно", "https://trigorskaya1.ru",
        "Гостевые дома «Терем Красный угол», «Отрада и Утешение» — бронь на сайте",
    ),
    (
        "Гостевой дом «Три Богатыря»", PlaceCategory.HOTEL,
        57.0255, 28.9155, "рп. Пушкинские Горы, ул. Пушкинская, 16Б",
        "+7 (911) 134-85-22", "по брони", "https://tribogatyrya-apart.ru",
        "Избы в старинном стиле, отдельный вход. strekoza-v@mail.ru",
    ),
    (
        "Гостевой дом «У лукоморья»", PlaceCategory.HOTEL,
        57.0385, 28.8940, "д. Шаробыки, ул. Тригорская, 1А",
        "+7 (921) 000-15-15", "круглосуточно", "https://ulukomorya.ru",
        "Дом «Псковские дали» — окраина Шаробик, рядом с заповедником",
    ),
    (
        "Бутик-отель «Усадьба по следам Онегина»", PlaceCategory.HOTEL,
        57.0305, 28.8870, "рп. Пушкинские Горы, около оз. Кучане",
        "+7 (911) 387-47-17", "круглосуточно", "https://usadba-onegina.ru",
        "Вид на Михайловское, 8 номеров в стиле пушкинской эпохи",
    ),
    (
        "Гостиница музея «Михайловское»", PlaceCategory.HOTEL,
        57.0282, 28.9075, "с. Михайловское, усадьба Михайловское",
        "+7 (81146) 2-23-21", "по брони", "https://pushkinland.ru",
        "Гостиница заповедника. Бронь: bilet1911@yandex.ru, +7 (81146) 2-26-09",
    ),
    (
        "Гостиница музея «Петровское»", PlaceCategory.HOTEL,
        57.0320, 28.8750, "с. Михайловское, усадьба Петровское",
        "+7 (81146) 2-23-21", "по брони", "https://pushkinland.ru",
        "У озера Кучане, 5 мин. пешком от усадьбы Ганнибалов",
    ),
    (
        "Гостиница «Пушкиногорская»", PlaceCategory.HOTEL,
        57.0278, 28.9105, "рп. Пушкинские Горы, ул. Красноармейская, 18",
        "+7 (81146) 2-13-50", "круглосуточно", None,
        "Гостиница в центре посёлка",
    ),
    (
        "Гостевой дом «Пушкиногорье» (турбаза)", PlaceCategory.HOTEL,
        57.0340, 28.9220, "рп. Пушкинские Горы, турбаза",
        "+7 (967) 555-90-13 (доб. 4908)", "круглосуточно", "https://pushkinogore.megotel.ru",
        "Апарт-отель на территории турбазы Пушкиногорье, от 1800 ₽",
    ),
    (
        "Гостевой дом с. Петровского", PlaceCategory.HOTEL,
        57.0315, 28.8740, "с. Михайловское, усадьба Петровское",
        "+7 (81146) 2-23-21", "по брони", "https://pushkinland.ru",
        "На берегу озера, рядом с усадьбой Петровское",
    ),

    # —— Посуточно (отдельная категория — не смешиваем с гостиницами) ——
    (
        "Квартиры посуточно — Авито", PlaceCategory.RENTAL,
        57.0267, 28.9100, "рп. Пушкинские Горы, центр",
        None, "актуально на Авито", "https://www.avito.ru/pushkinskie_gory/kvartiry/sdam/posutochno",
        "Все квартиры посуточно в посёлке — свежие объявления и номера на Авито",
    ),
    (
        "Дома и коттеджи посуточно — Авито", PlaceCategory.RENTAL,
        57.0267, 28.9100, "Пушкиногорский район",
        None, "актуально на Авито", "https://www.avito.ru/pushkinskie_gory/doma_dachi_kottedzhi/sdam/posutochno",
        "Дома, дачи и коттеджи посуточно по району — смотрите актуальные объявления",
    ),
    (
        "Квартира посуточно, ул. Ленина", PlaceCategory.RENTAL,
        57.0265, 28.9110, "рп. Пушкинские Горы, ул. Ленина",
        None, "от 2 суток", "https://www.avito.ru/pushkinskie_gory/kvartiry/sdam/posutochno",
        "Студии и квартиры в историческом центре — бронь через Авито",
    ),
    (
        "Дом посуточно, ул. Аэродромная, 1", PlaceCategory.RENTAL,
        57.0178, 28.9320, "рп. Пушкинские Горы, ул. Аэродромная, 1",
        None, "посуточно", "https://www.avito.ru/pushkinskie_gory/doma_dachi_kottedzhi/sdam/posutochno",
        "Дом с террасой и купелью — уточняйте номер на Авито",
    ),
    (
        "Дом посуточно, ул. Заозёрная, 48", PlaceCategory.RENTAL,
        57.0295, 28.9180, "рп. Пушкинские Горы, ул. Заозёрная, 48",
        None, "посуточно", "https://www.avito.ru/pushkinskie_gory/doma_dachi_kottedzhi/sdam/posutochno",
        "Дом в центре посёлка — актуальный контакт на Авито",
    ),
    (
        "Дача посуточно, д. Луговка", PlaceCategory.RENTAL,
        57.0400, 28.9300, "д. Луговка, менее 1 км от Пушкинских Гор",
        None, "посуточно", "https://www.avito.ru/pushkinskie_gory/doma_dachi_kottedzhi/sdam/posutochno",
        "Дача с 3 спальнями — бронь через объявление на Авито",
    ),
    (
        "Посуточно — Суточно.ру", PlaceCategory.RENTAL,
        57.0267, 28.9100, "Пушкиногорский район",
        None, "онлайн-бронь", "https://sutochno.ru/front/search?query=Пушкинские%20Горы",
        "Альтернатива Авито — посуточная аренда с онлайн-бронированием",
    ),
]


def _place_key(name: str, addr: str) -> str:
    digest = hashlib.md5(f"{name}|{addr}".encode()).hexdigest()[:20]
    return f"lodging_{digest}"


def _yandex_maps_url(lat: float, lng: float, name: str) -> str:
    from urllib.parse import quote
    return f"https://yandex.ru/maps/?pt={lng},{lat}&z=16&text={quote(name + ' Пушкиногорский район')}"


async def seed_lodging_places(db: AsyncSession) -> int:
    active_keys: set[str] = set()
    count = 0
    for row in LODGING_PLACES:
        name, cat, lat, lng, addr, phone, hours, website, desc = row
        key = _place_key(name, addr)
        active_keys.add(key)
        result = await db.execute(select(Place).where(Place.yandex_id == key))
        place = result.scalars().first()
        cat_label = PLACE_CATEGORY_LABELS.get(cat, "Проживание")

        if place:
            place.name = name
            place.category = cat
            place.latitude = lat
            place.longitude = lng
            place.address = addr
            place.phone = phone
            place.opening_hours = hours
            place.website = website
            place.description = desc
            place.external_source = "reference"
            place.external_rating = 0
            place.external_review_count = 0
            place.yandex_url = _yandex_maps_url(lat, lng, name)
            place.is_active = True
        else:
            db.add(Place(
                name=name, category=cat, latitude=lat, longitude=lng,
                address=addr, phone=phone, opening_hours=hours,
                website=website, description=desc,
                yandex_id=key, external_source="reference",
                yandex_url=_yandex_maps_url(lat, lng, name),
            ))
            count += 1

    ref_result = await db.execute(select(Place).where(Place.yandex_id.like("lodging_%")))
    for place in ref_result.scalars().all():
        if place.yandex_id and place.yandex_id not in active_keys:
            place.is_active = False

    await db.flush()
    return count

"""Справочник услуг посёлка и ссылки на Авито."""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_item import CatalogItem
from app.models.enums import CatalogCategory, CatalogSource, CATALOG_CATEGORY_LABELS

AVITO_BASE = "https://www.avito.ru/pushkinskie_gory"

# name, category, description, phone, url, price_hint, address, source
CATALOG_SEED: list[tuple] = [
    (
        "Перепахать огород",
        CatalogCategory.GARDEN,
        "Вспашка, культивация, подготовка грядок — ищите исполнителей на Авито и в объявлениях соседей",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug/predlozheniya_uslug_dlya_doma-ASgBAgICAkQeAUP0lg",
        "договорная",
        "Пушкинские Горы",
        CatalogSource.AVITO,
    ),
    (
        "Покос травы / газона",
        CatalogCategory.GRASS_MOWING,
        "Покос участков, триммер, вывоз травы — типичная услуга в посёлке летом",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug",
        "от 500 ₽",
        "Пушкиногорский район",
        CatalogSource.REFERENCE,
    ),
    (
        "Дрова / колка / доставка",
        CatalogCategory.FIREWOOD,
        "Колка, заготовка и доставка дров — смотрите объявления соседей и Авито",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug",
        "договорная",
        "Пушкинские Горы",
        CatalogSource.REFERENCE,
    ),
    (
        "Уборка снега",
        CatalogCategory.SNOW_REMOVAL,
        "Чистка крыш, дорожек, парковок — сезонная услуга",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug/uborka-ASgBAgICAUTEA0T0lg",
        "договорная",
        "Пушкинские Горы",
        CatalogSource.AVITO,
    ),
    (
        "Мелкий ремонт, сантехника, электрика",
        CatalogCategory.HANDYMAN,
        "Муж на час, мелкий бытовой ремонт в доме и на участке",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug/remont_stroitelstvo-ASgBAgICAkTeDQL0lg",
        "договорная",
        None,
        CatalogSource.AVITO,
    ),
    (
        "Строительство / ремонт",
        CatalogCategory.CONSTRUCTION,
        "Отделка, кровля, фундамент, баня — предложения на Авито по району",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug/remont_stroitelstvo-ASgBAgICAkTeDQL0lg",
        None,
        "Пушкиногорский район",
        CatalogSource.AVITO,
    ),
    (
        "Доставка / вывоз / грузчики",
        CatalogCategory.DELIVERY,
        "Доставка стройматериалов, вывоз мусора, погрузка",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug/perevozki_i_gruzoperevozki-ASgBAgICAkQeAUX0lg",
        None,
        None,
        CatalogSource.AVITO,
    ),
    (
        "Репетитор / обучение",
        CatalogCategory.TUTORING,
        "Занятия для детей и взрослых — объявления на портале и Авито",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug",
        None,
        None,
        CatalogSource.REFERENCE,
    ),
    (
        "Услуги посёлка — все на Авито",
        CatalogCategory.AVITO,
        "Актуальные объявления исполнителей: перепашка, покос, ремонт, доставка",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug",
        "актуально на сайте",
        "Пушкинские Горы",
        CatalogSource.AVITO,
    ),
    (
        "Для дома и дачи — Авито",
        CatalogCategory.AVITO,
        "Огород, баня, забор, благоустройство участка",
        None,
        f"{AVITO_BASE}/predlozheniya_uslug/predlozheniya_uslug_dlya_doma-ASgBAgICAkQeAUP0lg",
        None,
        "Пушкиногорский район",
        CatalogSource.AVITO,
    ),
]


def _seed_key(name: str, category: str) -> str:
    digest = hashlib.md5(f"{name}|{category}".encode()).hexdigest()[:20]
    return f"svc_{digest}"


async def seed_village_services(db: AsyncSession) -> int:
    active_keys: set[str] = set()
    created = 0
    for row in CATALOG_SEED:
        name, cat, desc, phone, url, price, addr, src = row
        key = _seed_key(name, cat.value)
        active_keys.add(key)
        result = await db.execute(select(CatalogItem).where(CatalogItem.seed_key == key))
        item = result.scalars().first()
        if item:
            item.name = name
            item.category = cat
            item.description = desc
            item.phone = phone
            item.external_url = url
            item.price_hint = price
            item.address = addr
            item.source = src
            item.is_internal = False
            item.is_active = True
        else:
            db.add(CatalogItem(
                name=name,
                category=cat,
                description=desc,
                phone=phone,
                external_url=url,
                price_hint=price,
                address=addr,
                source=src,
                seed_key=key,
                sort_order=10 if src == CatalogSource.AVITO else 50,
            ))
            created += 1

    stale = await db.execute(select(CatalogItem).where(CatalogItem.seed_key.like("svc_%")))
    for item in stale.scalars().all():
        if item.seed_key and item.seed_key not in active_keys:
            item.is_active = False

    await db.flush()
    return created

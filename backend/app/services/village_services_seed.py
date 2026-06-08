"""Справочник услуг посёлка — без внешних агрегаторов."""

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_item import CatalogItem
from app.models.enums import CatalogCategory, CatalogSource, CATALOG_CATEGORY_LABELS

# name, category, description, phone, url, price_hint, address, source
CATALOG_SEED: list[tuple] = [
    (
        "Перепахать огород",
        CatalogCategory.GARDEN,
        "Вспашка, культивация, подготовка грядок — смотрите объявления соседей на портале",
        None, None, "договорная", "Пушкинские Горы", CatalogSource.REFERENCE,
    ),
    (
        "Покос травы / газона",
        CatalogCategory.GRASS_MOWING,
        "Покос участков, триммер, вывоз травы — типичная услуга в посёлке летом",
        None, None, "от 500 ₽", "Пушкиногорский район", CatalogSource.REFERENCE,
    ),
    (
        "Дрова / колка / доставка",
        CatalogCategory.FIREWOOD,
        "Колка, заготовка и доставка дров — объявления соседей в разделе «Объявления»",
        None, None, "договорная", "Пушкинские Горы", CatalogSource.REFERENCE,
    ),
    (
        "Уборка снега",
        CatalogCategory.SNOW_REMOVAL,
        "Чистка крыш, дорожек, парковок — сезонная услуга",
        None, None, "договорная", "Пушкинские Горы", CatalogSource.REFERENCE,
    ),
    (
        "Мелкий ремонт, сантехника, электрика",
        CatalogCategory.HANDYMAN,
        "Муж на час, мелкий бытовой ремонт в доме и на участке",
        None, None, "договорная", None, CatalogSource.REFERENCE,
    ),
    (
        "Строительство / ремонт",
        CatalogCategory.CONSTRUCTION,
        "Отделка, кровля, фундамент, баня — мастера и бригады по району",
        None, None, None, "Пушкиногорский район", CatalogSource.REFERENCE,
    ),
    (
        "Доставка / вывоз / грузчики",
        CatalogCategory.DELIVERY,
        "Доставка стройматериалов, вывоз мусора, погрузка",
        None, None, None, None, CatalogSource.REFERENCE,
    ),
    (
        "Репетитор / обучение",
        CatalogCategory.TUTORING,
        "Занятия для детей и взрослых — объявления на портале",
        None, None, None, None, CatalogSource.REFERENCE,
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
                sort_order=50,
            ))
            created += 1

    stale = await db.execute(select(CatalogItem).where(CatalogItem.seed_key.like("svc_%")))
    for item in stale.scalars().all():
        if item.seed_key and item.seed_key not in active_keys:
            item.is_active = False

    await db.flush()
    return created

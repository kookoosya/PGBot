"""Проверки и очистка карты: дубли, банки, мусор OSM/Yandex."""

import logging
import math
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_item import CatalogItem
from app.models.enums import CatalogCategory, CatalogSource, PlaceCategory
from app.models.place import Place

logger = logging.getLogger(__name__)

SKIP_OSM_NAMES = {
    "ozon", "wildberries", "сдэк", "cdek", "pickpoint", "boxberry",
    "exclusive palace", "пункт выдачи", "postamat", "постамат", "пропан",
    "т-банк", "t-bank", "tinkoff", "тинькофф", "tbank",
    "втб", "альфа-банк", "райффайзен", "газпромбанк", "открытие",
    "россельхоз", "совкомбанк", "мкб",
}
DEPRECATED_ADDRESS_PARTS = (
    "строителей, 1-б",
    "строителей, 1",
    "лермонтова, 10",
    "лермонтова, 42",
    "красноармейская",
)
SKIP_OSM_SHOPS = {"parcel_locker", "outpost", "kiosk", "ticket", "lottery"}
SKIP_OSM_AMENITIES = {"parcel_locker", "vending_machine", "atm", "bank"}

# Радиус, в котором OSM/Yandex считается дублем справочника
REF_DEDUP_KM = 0.15

# В посёлке один банкомат — только reference «Сбербанк»
ALLOWED_BANK_NAME_TOKENS = ("сбер", "900")

YANDEX_SKIP_NAME_FRAGMENTS = SKIP_OSM_NAMES | {
    "банкомат", "atm", "криптомат",
}


def _norm_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").lower().replace("«", "").replace("»", "").strip())


def _names_overlap(a: str, b: str) -> bool:
    na, nb = _norm_name(a), _norm_name(b)
    if not na or not nb:
        return False
    if na == nb or na in nb or nb in na:
        return True
    words_a = {w for w in na.split() if len(w) > 3}
    words_b = {w for w in nb.split() if len(w) > 3}
    if words_a & words_b:
        return True
    if "косметик" in na and "косметик" in nb:
        return True
    return False


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _is_junk_name(name: str) -> bool:
    name_l = _norm_name(name)
    return any(skip in name_l for skip in YANDEX_SKIP_NAME_FRAGMENTS)


def _is_allowed_reference_bank(name: str) -> bool:
    name_l = _norm_name(name)
    return any(token in name_l for token in ALLOWED_BANK_NAME_TOKENS)


def _fix_category(name: str, category: PlaceCategory) -> PlaceCategory:
    """Исправить типовые ошибки категоризации из OSM/Yandex."""
    name_l = _norm_name(name)
    if "косметик" in name_l and category == PlaceCategory.BANK:
        return PlaceCategory.BEAUTY
    if "косметик" in name_l and category in (PlaceCategory.OTHER, PlaceCategory.SHOP):
        return PlaceCategory.BEAUTY
    if "магнит" in name_l and "косметик" in name_l:
        return PlaceCategory.BEAUTY
    return category


def _nearby_reference(
    place: Place,
    reference: list[Place],
    *,
    radius_km: float = REF_DEDUP_KM,
) -> Place | None:
    """Найти справочную точку рядом с тем же смыслом (имя или категория сети)."""
    brand = _norm_name(place.name)
    for ref in reference:
        if _distance_km(place.latitude, place.longitude, ref.latitude, ref.longitude) > radius_km:
            continue
        if _names_overlap(place.name, ref.name):
            return ref
        if place.category == ref.category:
            ref_brand = _norm_name(ref.name)
            for token in ("пятёрочка", "пятерочка", "магнит", "аптека", "сбер"):
                if token in brand and token in ref_brand:
                    return ref
            # Один объект на категорию в центре посёлка (банк, почта, МФЦ…)
            if place.category in (
                PlaceCategory.BANK,
                PlaceCategory.POST,
                PlaceCategory.GOVERNMENT,
                PlaceCategory.HOSPITAL,
                PlaceCategory.TRANSPORT,
            ):
                return ref
    return None


def should_skip_yandex_org(name: str, categories: list | None = None) -> bool:
    """Не импортировать банки/мусор из Яндекс.Карт — банк только из справочника."""
    if _is_allowed_reference_bank(name):
        return False
    if _is_junk_name(name):
        return True
    name_l = _norm_name(name)
    if "банкомат" in name_l:
        if not _is_allowed_reference_bank(name):
            return True
    elif "банк" in name_l and not _is_allowed_reference_bank(name):
        return True
    for cat in categories or []:
        cn = _norm_name((cat.get("name") if isinstance(cat, dict) else str(cat)) or "")
        if "банк" in cn and not _is_allowed_reference_bank(name):
            return True
    return False


async def deactivate_stale_imports(
    db: AsyncSession,
    source: str,
    sync_started: datetime,
) -> int:
    """Снять с карты POI из OSM/Yandex, которых не было в последнем проходе синка."""
    from sqlalchemy import or_

    result = await db.execute(
        select(Place).where(
            Place.external_source == source,
            Place.is_active.is_(True),
            or_(Place.last_synced_at.is_(None), Place.last_synced_at < sync_started),
        )
    )
    count = 0
    for place in result.scalars().all():
        place.is_active = False
        count += 1
    if count:
        logger.info("Stale %s places deactivated: %d", source, count)
    await db.flush()
    return count


def match_reference_import(
    name: str,
    lat: float,
    lng: float,
    reference: list[Place],
    *,
    radius_km: float = REF_DEDUP_KM,
) -> Place | None:
    """Сопоставить импорт OSM/Yandex со справочной точкой (без дубля)."""
    probe = Place(
        name=name,
        latitude=lat,
        longitude=lng,
        category=_fix_category(name, PlaceCategory.OTHER),
    )
    return _nearby_reference(probe, reference, radius_km=radius_km)


async def cleanup_map_places(db: AsyncSession) -> dict:
    """Деактивируем мусор, лишние банки и дубли справочника."""
    deactivated = 0
    fixed_category = 0
    result = await db.execute(select(Place))
    places = list(result.scalars().all())
    reference = [p for p in places if p.external_source == "reference" and p.is_active]

    for place in places:
        if not place.is_active:
            continue

        new_cat = _fix_category(place.name, place.category)
        if new_cat != place.category:
            place.category = new_cat
            fixed_category += 1

        reason = None

        website = (place.website or "").lower()
        if "avito.ru" in website or "sutochno.ru" in website:
            reason = "aggregator"
        elif place.category == PlaceCategory.RENTAL:
            reason = "rental_removed"
        elif any(part in (place.address or "").lower() for part in DEPRECATED_ADDRESS_PARTS):
            reason = "deprecated_address"
        elif place.category == PlaceCategory.GAS and "пропан" in _norm_name(place.name):
            reason = "propane_not_petrol"
        elif place.external_source == "seed":
            reason = "legacy_seed"
        elif place.category == PlaceCategory.BANK:
            if place.external_source != "reference" or not _is_allowed_reference_bank(place.name):
                reason = "bank_not_reference"
        elif _is_junk_name(place.name):
            reason = "junk_name"
        elif place.external_source in ("osm", "yandex"):
            name_l = _norm_name(place.name)
            if any(skip in name_l for skip in SKIP_OSM_NAMES):
                reason = "osm_junk_name"
            elif not place.address and not place.phone:
                reason = "osm_no_contact"
            elif place.category in (
                PlaceCategory.SUPERMARKET,
                PlaceCategory.PHARMACY,
                PlaceCategory.GAS,
            ) and not place.address:
                reason = "unverified_no_address"
            elif _nearby_reference(place, reference):
                reason = "duplicate_ref_nearby"

        if reason:
            place.is_active = False
            deactivated += 1

    osm_active = [p for p in places if p.is_active and p.external_source == "osm"]
    for i, a in enumerate(osm_active):
        if not a.is_active:
            continue
        for b in osm_active[i + 1 :]:
            if not b.is_active:
                continue
            if _norm_name(a.name) == _norm_name(b.name) and _distance_km(
                a.latitude, a.longitude, b.latitude, b.longitude
            ) < 0.08:
                loser = a if not a.address and b.address else b if not b.address and a.address else b
                loser.is_active = False
                deactivated += 1

    cat_result = await db.execute(select(CatalogItem))
    catalog_off = 0
    for item in cat_result.scalars().all():
        if item.source == CatalogSource.AVITO or item.category == CatalogCategory.AVITO:
            if item.is_active:
                item.is_active = False
                catalog_off += 1
        elif item.external_url and "avito.ru" in item.external_url.lower():
            item.external_url = None
            item.source = CatalogSource.REFERENCE

    await db.flush()
    logger.info(
        "Map cleanup: %d places deactivated, %d categories fixed, %d catalog off",
        deactivated,
        fixed_category,
        catalog_off,
    )
    return {
        "places_deactivated": deactivated,
        "categories_fixed": fixed_category,
        "catalog_deactivated": catalog_off,
    }


def should_skip_osm_element(tags: dict, name: str) -> bool:
    """Не импортировать пункты выдачи, банки/ATM и объекты без адреса."""
    name_l = _norm_name(name)
    brand = _norm_name(tags.get("brand") or "")
    if any(skip in name_l or skip in brand for skip in SKIP_OSM_NAMES):
        return True
    if tags.get("shop") in SKIP_OSM_SHOPS:
        return True
    if tags.get("amenity") in SKIP_OSM_AMENITIES:
        return True
    if tags.get("amenity") == "bank" or tags.get("amenity") == "atm":
        return True
    if tags.get("vending") == "parcel_pickup":
        return True
    if not _build_address(tags) and not tags.get("addr:street"):
        return True
    return False


def _build_address(tags: dict) -> str | None:
    parts = []
    for key in ("addr:street", "addr:housenumber", "addr:city"):
        if tags.get(key):
            parts.append(tags[key])
    if parts:
        return ", ".join(parts)
    return tags.get("addr:full")

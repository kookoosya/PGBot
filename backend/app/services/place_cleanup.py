"""Очистка карты: убираем Авито, дубли и мусор из OSM."""

import logging
import math
import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_item import CatalogItem
from app.models.enums import CatalogCategory, CatalogSource, PlaceCategory
from app.models.place import Place

logger = logging.getLogger(__name__)

SKIP_OSM_NAMES = {
    "ozon", "wildberries", "сдэк", "cdek", "pickpoint", "boxberry",
    "exclusive palace", "пункт выдачи", "постамат", "пропан",
}
DEPRECATED_ADDRESS_PARTS = ("строителей, 1-б", "строителей, 1")
SKIP_OSM_SHOPS = {"parcel_locker", "outpost", "kiosk", "ticket", "lottery"}
SKIP_OSM_AMENITIES = {"parcel_locker", "vending_machine"}


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
    return bool(words_a & words_b)


def _distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


async def cleanup_map_places(db: AsyncSession) -> dict:
    """Деактивируем Авито, посуточку-агрегаторы, мусор OSM и дубли."""
    deactivated = 0
    result = await db.execute(select(Place))
    places = list(result.scalars().all())
    reference = [p for p in places if p.external_source == "reference" and p.is_active]

    for place in places:
        if not place.is_active:
            continue
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
        elif place.external_source == "osm":
            name_l = _norm_name(place.name)
            if any(skip in name_l for skip in SKIP_OSM_NAMES):
                reason = "osm_junk_name"
            elif not place.address and not place.phone:
                reason = "osm_no_contact"
            else:
                for ref in reference:
                    if (
                        _distance_km(place.latitude, place.longitude, ref.latitude, ref.longitude) < 0.2
                        and (_names_overlap(place.name, ref.name) or place.category == ref.category)
                    ):
                        reason = "osm_duplicate_ref"
                        break

        if reason:
            place.is_active = False
            deactivated += 1

    # Дубли OSM: одно имя в радиусе 80 м — оставляем с адресом
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

    # Каталог: убираем Авито
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
    logger.info("Map cleanup: %d places deactivated, %d catalog items off", deactivated, catalog_off)
    return {"places_deactivated": deactivated, "catalog_deactivated": catalog_off}


def should_skip_osm_element(tags: dict, name: str) -> bool:
    """Не импортировать пункты выдачи и объекты без адреса."""
    name_l = _norm_name(name)
    brand = _norm_name(tags.get("brand") or "")
    if any(skip in name_l or skip in brand for skip in SKIP_OSM_NAMES):
        return True
    if tags.get("shop") in SKIP_OSM_SHOPS:
        return True
    if tags.get("amenity") in SKIP_OSM_AMENITIES:
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

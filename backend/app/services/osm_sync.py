import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import PLACE_CATEGORY_LABELS, PlaceCategory
from app.models.place import Place

logger = logging.getLogger(__name__)
settings = get_settings()

# Pushkinogorsky district bounding box (expanded)
BBOX = "57.00,28.75,57.15,29.10"

OSM_TAG_TO_CATEGORY = {
    "shop": PlaceCategory.SHOP,
    "supermarket": PlaceCategory.SUPERMARKET,
    "convenience": PlaceCategory.SHOP,
    "general": PlaceCategory.SHOP,
    "bakery": PlaceCategory.SHOP,
    "butcher": PlaceCategory.SHOP,
    "pharmacy": PlaceCategory.PHARMACY,
    "cafe": PlaceCategory.CAFE,
    "restaurant": PlaceCategory.RESTAURANT,
    "fast_food": PlaceCategory.CAFE,
    "bank": PlaceCategory.BANK,
    "atm": PlaceCategory.BANK,
    "post_office": PlaceCategory.POST,
    "school": PlaceCategory.SCHOOL,
    "kindergarten": PlaceCategory.SCHOOL,
    "hospital": PlaceCategory.HOSPITAL,
    "clinic": PlaceCategory.HOSPITAL,
    "doctors": PlaceCategory.HOSPITAL,
    "townhall": PlaceCategory.GOVERNMENT,
    "library": PlaceCategory.CULTURE,
    "museum": PlaceCategory.CULTURE,
    "theatre": PlaceCategory.CULTURE,
    "hotel": PlaceCategory.HOTEL,
    "guest_house": PlaceCategory.HOTEL,
    "fuel": PlaceCategory.GAS,
    "bus_station": PlaceCategory.TRANSPORT,
    "hairdresser": PlaceCategory.BEAUTY,
    "beauty": PlaceCategory.BEAUTY,
    "nails": PlaceCategory.BEAUTY,
    "spa": PlaceCategory.BEAUTY,
    "tyres": PlaceCategory.TYRE,
    "car_repair": PlaceCategory.AUTO,
    "car": PlaceCategory.AUTO,
    "garage": PlaceCategory.AUTO,
}

OVERPASS_QUERY = """
[out:json][timeout:60];
(
  node["shop"]({bbox});
  node["amenity"~"pharmacy|cafe|restaurant|fast_food|bank|post_office|school|kindergarten|hospital|clinic|doctors|townhall|library|museum|theatre|fuel|bus_station|hairdresser|beauty|spa|car_repair"]({bbox});
  node["shop"~"hairdresser|beauty|cosmetics|tyres|car|car_repair"]({bbox});
  node["tourism"~"hotel|guest_house|museum"]({bbox});
  way["shop"]({bbox});
  way["amenity"~"pharmacy|cafe|restaurant|supermarket|hospital|townhall|library|museum"]({bbox});
);
out center;
"""


def _map_category(tags: dict) -> PlaceCategory:
    if shop := tags.get("shop"):
        return OSM_TAG_TO_CATEGORY.get(shop, PlaceCategory.SHOP)
    if amenity := tags.get("amenity"):
        return OSM_TAG_TO_CATEGORY.get(amenity, PlaceCategory.OTHER)
    if tourism := tags.get("tourism"):
        return OSM_TAG_TO_CATEGORY.get(tourism, PlaceCategory.OTHER)
    return PlaceCategory.OTHER


def _build_address(tags: dict) -> str | None:
    parts = []
    for key in ("addr:street", "addr:housenumber", "addr:city"):
        if tags.get(key):
            parts.append(tags[key])
    if parts:
        return ", ".join(parts)
    return tags.get("addr:full")


async def sync_places_from_osm(db: AsyncSession) -> dict:
    """Fetch POIs from OpenStreetMap and upsert into database."""
    query = OVERPASS_QUERY.format(bbox=BBOX)
    synced = created = updated = 0

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                "https://overpass-api.de/api/interpreter",
                content=query,
                headers={
                    "Content-Type": "text/plain; charset=utf-8",
                    "User-Agent": "NarodnyKontrol-PushkinGory/1.0 (contact: support@pushkinskie-gory.local)",
                },
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.error("OSM sync failed: %s", e)
        return {"error": str(e), "synced": 0}

    now = datetime.now(timezone.utc)

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name") or tags.get("name:ru") or tags.get("brand")
        if not name:
            continue

        lat = element.get("lat") or (element.get("center") or {}).get("lat")
        lon = element.get("lon") or (element.get("center") or {}).get("lon")
        if not lat or not lon:
            continue

        osm_id = f"{element['type']}/{element['id']}"
        category = _map_category(tags)

        result = await db.execute(select(Place).where(Place.osm_id == osm_id))
        place = result.scalar_one_or_none()

        hours = tags.get("opening_hours")
        phone = tags.get("phone") or tags.get("contact:phone")
        website = tags.get("website") or tags.get("contact:website")

        if place:
            place.name = name
            place.category = category
            place.address = _build_address(tags) or place.address
            place.latitude = lat
            place.longitude = lon
            place.phone = phone or place.phone
            place.website = website or place.website
            place.opening_hours = hours or place.opening_hours
            place.last_synced_at = now
            place.external_source = "osm"
            updated += 1
        else:
            cat_label = PLACE_CATEGORY_LABELS.get(category, "Объект")
            db.add(Place(
                name=name,
                category=category,
                description=f"{cat_label} — данные OpenStreetMap",
                address=_build_address(tags),
                latitude=lat,
                longitude=lon,
                phone=phone,
                website=website,
                opening_hours=hours,
                osm_id=osm_id,
                external_source="osm",
                last_synced_at=now,
            ))
            created += 1
        synced += 1

    await db.flush()
    logger.info("OSM sync: %d total, %d new, %d updated", synced, created, updated)
    return {"synced": synced, "created": created, "updated": updated}


async def seed_pushkin_landmarks(db: AsyncSession) -> int:
    """Seed key Pushkinogorsky landmarks if not present."""
    landmarks = [
        ("Музей-заповедник А.С. Пушкина «Михайловское»", PlaceCategory.CULTURE, 57.028, 28.908, "Пушкиногорский р-н, с. Пушкинские Горы"),
        ("Государственный музей-заповедник А.С. Пушкина", PlaceCategory.CULTURE, 57.027, 28.909, "Пушкинские Горы, ул. Красноармейская"),
        ("Свято-Успенская Пушкиногорская лавра", PlaceCategory.CULTURE, 57.025, 28.912, "Пушкинские Горы"),
        ("Администрация Пушкиногорского района", PlaceCategory.GOVERNMENT, 57.026, 28.911, "Пушкинские Горы, пл. Ленина"),
        ("Пушкиногорская ЦРБ", PlaceCategory.HOSPITAL, 57.024, 28.915, "Пушкинские Горы"),
        ("Магазин «Пятёрочка»", PlaceCategory.SUPERMARKET, 57.027, 28.910, "Пушкинские Горы, ул. Красноармейская"),
        ("Магазин «Магнит»", PlaceCategory.SUPERMARKET, 57.026, 28.908, "Пушкинские Горы"),
        ("Аптека", PlaceCategory.PHARMACY, 57.0265, 28.9095, "Пушкинские Горы, центр"),
        ("Автовокзал Пушкинские Горы", PlaceCategory.TRANSPORT, 57.028, 28.905, "Пушкинские Горы"),
        ("Сбербанк", PlaceCategory.BANK, 57.0268, 28.9105, "Пушкинские Горы"),
    ]
    count = 0
    for name, cat, lat, lng, addr in landmarks:
        result = await db.execute(select(Place).where(Place.name == name, Place.address == addr))
        if not result.scalar_one_or_none():
            db.add(Place(
                name=name, category=cat, latitude=lat, longitude=lng,
                address=addr, description=f"Пушкиногорский район — {PLACE_CATEGORY_LABELS.get(cat, '')}",
                external_source="seed",
            ))
            count += 1
    await db.flush()
    return count

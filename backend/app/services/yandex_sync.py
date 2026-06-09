import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import PLACE_CATEGORY_LABELS, PlaceCategory
from app.models.place import Place
from app.services.pushkin_places_seed import seed_village_places

logger = logging.getLogger(__name__)
settings = get_settings()

YANDEX_SEARCH_URL = "https://search-maps.yandex.ru/v1/"

SEARCH_QUERIES = [
    "аптека Пушкинские Горы",
    "магазин Пушкинские Горы",
    "супермаркет Пушкинские Горы",
    "шиномонтаж Пушкинские Горы",
    "шиномонтаж Аэродромная Пушкинские Горы",
    "заправка Новоржевская Пушкинские Горы",
    "автосервис Пушкинские Горы",
    "кафе Пушкинские Горы",
    "ресторан Пушкинские Горы",
    "гостиница Пушкинские Горы",
    "гостевой дом Пушкиногорский район",
    "база отдыха Пушкинские Горы",
    "банк Пушкинские Горы",
    "АЗС Пушкинские Горы",
    "парикмахерская Пушкинские Горы",
    "почта Пушкинские Горы",
]

YANDEX_CAT_MAP = {
    "аптека": PlaceCategory.PHARMACY,
    "магазин": PlaceCategory.SHOP,
    "супермаркет": PlaceCategory.SUPERMARKET,
    "продукт": PlaceCategory.SHOP,
    "шиномонтаж": PlaceCategory.TYRE,
    "автосервис": PlaceCategory.AUTO,
    "сто": PlaceCategory.AUTO,
    "кафе": PlaceCategory.CAFE,
    "ресторан": PlaceCategory.RESTAURANT,
    "гостиница": PlaceCategory.HOTEL,
    "отель": PlaceCategory.HOTEL,
    "гостевой": PlaceCategory.HOTEL,
    "турбаз": PlaceCategory.HOTEL,
    "посуточно": PlaceCategory.RENTAL,
    "аренда": PlaceCategory.RENTAL,
    "банк": PlaceCategory.BANK,
    "азс": PlaceCategory.GAS,
    "заправка": PlaceCategory.GAS,
    "парикмахерская": PlaceCategory.BEAUTY,
    "салон": PlaceCategory.BEAUTY,
    "почта": PlaceCategory.POST,
    "музей": PlaceCategory.CULTURE,
    "школа": PlaceCategory.SCHOOL,
    "больница": PlaceCategory.HOSPITAL,
    "поликлиника": PlaceCategory.HOSPITAL,
}


def _guess_category(name: str, categories: list) -> PlaceCategory:
    text = name.lower()
    for cat_names in categories:
        cn = (cat_names.get("name") or "").lower()
        for key, val in YANDEX_CAT_MAP.items():
            if key in cn or key in text:
                return val
    for key, val in YANDEX_CAT_MAP.items():
        if key in text:
            return val
    return PlaceCategory.OTHER


def _parse_rating(meta: dict) -> tuple[float, int]:
    rating_block = meta.get("Rating") or meta.get("rating") or {}
    score = rating_block.get("score") or rating_block.get("value") or 0
    reviews = rating_block.get("reviewCount") or rating_block.get("reviews") or rating_block.get("count") or 0
    try:
        return round(float(score), 1), int(reviews)
    except (TypeError, ValueError):
        return 0.0, 0


async def sync_places_from_yandex(db: AsyncSession) -> dict:
    if not settings.YANDEX_MAPS_API_KEY:
        seeded = await seed_village_places(db)
        return {"source": "reference_seed", "synced": seeded, "api": False}

    synced = created = updated = 0
    now = datetime.now(UTC)
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(timeout=30) as client:
        for query in SEARCH_QUERIES:
            try:
                response = await client.get(
                    YANDEX_SEARCH_URL,
                    params={
                        "apikey": settings.YANDEX_MAPS_API_KEY,
                        "text": query,
                        "type": "biz",
                        "lang": "ru_RU",
                        "results": 50,
                        "ll": f"{settings.MAP_CENTER_LNG},{settings.MAP_CENTER_LAT}",
                        "spn": "0.12,0.10",
                    },
                )
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                logger.warning("Yandex search failed for %s: %s", query, exc)
                continue

            for feature in data.get("features", []):
                props = feature.get("properties", {})
                meta = props.get("CompanyMetaData") or {}
                yid = meta.get("id")
                name = meta.get("name")
                if not yid or not name or yid in seen_ids:
                    continue
                seen_ids.add(yid)

                coords = feature.get("geometry", {}).get("coordinates", [])
                if len(coords) < 2:
                    continue
                lng, lat = coords[0], coords[1]

                address = meta.get("address") or (meta.get("Address") or {}).get("formatted")
                phone = None
                for c in meta.get("Phones") or []:
                    phone = c.get("formatted") or c.get("number")
                    if phone:
                        break
                hours = (meta.get("Hours") or {}).get("text")
                cats = meta.get("Categories") or []
                category = _guess_category(name, cats)
                rating, reviews = _parse_rating(meta)
                yandex_url = props.get("uri") or meta.get("url")

                result = await db.execute(select(Place).where(Place.yandex_id == str(yid)))
                place = result.scalar_one_or_none()
                if place:
                    place.name = name
                    place.category = category
                    place.address = address or place.address
                    place.latitude = lat
                    place.longitude = lng
                    place.phone = phone or place.phone
                    place.opening_hours = hours or place.opening_hours
                    place.external_rating = rating or place.external_rating
                    place.external_review_count = reviews or place.external_review_count
                    place.yandex_url = yandex_url
                    place.external_source = "yandex"
                    place.last_synced_at = now
                    updated += 1
                else:
                    cat_label = PLACE_CATEGORY_LABELS.get(category, "Объект")
                    db.add(
                        Place(
                            name=name,
                            category=category,
                            latitude=lat,
                            longitude=lng,
                            address=address,
                            phone=phone,
                            opening_hours=hours,
                            description=f"{cat_label} — Яндекс.Карты",
                            yandex_id=str(yid),
                            yandex_url=yandex_url,
                            external_source="yandex",
                            external_rating=rating,
                            external_review_count=reviews,
                            last_synced_at=now,
                        )
                    )
                    created += 1
                synced += 1

    await db.flush()
    if synced == 0:
        seeded = await seed_village_places(db)
        return {"source": "reference_fallback", "synced": seeded, "api": True, "error": "no_results"}

    logger.info("Yandex sync: %d total, %d new, %d updated", synced, created, updated)
    return {"source": "yandex", "synced": synced, "created": created, "updated": updated, "api": True}

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.osm_sync import seed_pushkin_landmarks, sync_places_from_osm
from app.services.lodging_seed import seed_lodging_places
from app.services.place_cleanup import cleanup_map_places
from app.services.village_services_seed import seed_village_services
from app.services.pushkin_places_seed import seed_taxi_services, seed_village_places
from app.services.yandex_sync import sync_places_from_yandex

logger = logging.getLogger(__name__)


async def sync_all_map_data(db: AsyncSession) -> dict:
    """Full map refresh: reference data, OSM, Yandex/reference ratings, taxi."""
    results = {}
    results["landmarks"] = await seed_pushkin_landmarks(db)
    results["village"] = await seed_village_places(db)
    results["lodging"] = await seed_lodging_places(db)
    results["village_services"] = await seed_village_services(db)
    results["taxi"] = await seed_taxi_services(db)
    results["osm"] = await sync_places_from_osm(db)
    results["yandex"] = await sync_places_from_yandex(db)
    results["cleanup"] = await cleanup_map_places(db)
    return results

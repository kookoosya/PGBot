from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas.today import TodayResponse
from app.services.today_service import build_today_snapshot

router = APIRouter()
settings = get_settings()


def _vk_bot_ready() -> bool:
    url = (settings.VK_GROUP_URL or "").rstrip("/")
    token = (settings.VK_GROUP_TOKEN or "").strip()
    if not token or token.startswith("your-"):
        return False
    return url not in ("", "https://vk.com", "http://vk.com")


@router.get("/info")
async def public_info():
    site = settings.PUBLIC_SITE_URL.rstrip("/")
    vk_url = settings.VK_GROUP_URL.rstrip("/") if settings.VK_GROUP_URL else "https://vk.com"
    ready = _vk_bot_ready()
    return {
        "site_url": site,
        "vk_url": vk_url,
        "vk_bot_ready": ready,
        "vk_bot_hint": (
            "Напишите «Начать» в сообщениях сообщества — бот ответит кнопками: карта, такси, гостиницы."
            if ready
            else "Бот живёт в личных сообщениях сообщества ВКонтакте. Попросите администратора портала дать прямую ссылку."
        ),
        "map_url": f"{site}/map",
        "yandex_maps_add_org": "https://yandex.ru/sprav/add",
    }


@router.get("/today", response_model=TodayResponse)
async def today_in_village(db: Annotated[AsyncSession, Depends(get_db)]):
    """Aggregated landing snapshot: weather, latest ad, map stats."""
    snapshot = await build_today_snapshot(db)
    return snapshot.to_response()

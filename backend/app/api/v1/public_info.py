from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/info")
async def public_info():
    site = settings.PUBLIC_SITE_URL.rstrip("/")
    return {
        "site_url": site,
        "vk_url": settings.VK_GROUP_URL,
        "map_url": f"{site}/map",
        "yandex_maps_add_org": "https://yandex.ru/sprav/add",
    }

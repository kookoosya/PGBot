"""Ответы бота по ключевым словам карты и справочнику мест."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import PlaceCategory
from app.models.place import Place
from app.models.taxi import TaxiService
from app.services.vk import get_welcome_keyboard, send_message

settings = get_settings()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")


async def reply_places(
    db: AsyncSession,
    peer_id: int,
    *,
    category: PlaceCategory | None = None,
    categories: tuple[PlaceCategory, ...] | None = None,
    search: str | None = None,
) -> None:
    """Найти места в справочнике и отправить список."""
    query = select(Place).where(Place.is_active.is_(True))
    if categories:
        query = query.where(Place.category.in_(categories))
    elif category:
        query = query.where(Place.category == category)
    if search:
        query = query.where(Place.name.ilike(f"%{search}%") | Place.address.ilike(f"%{search}%"))
    result = await db.execute(query.order_by(Place.name).limit(6))
    places = result.scalars().all()
    if not places:
        await send_message(
            peer_id,
            f"Пока не нашёл в справочнике. Откройте карту:\n{_SITE}/map",
            keyboard=get_welcome_keyboard(),
        )
        return
    lines = ["🗺 На карте посёлка:\n"]
    for place in places:
        lines.append(f"• {place.name}")
        if place.address:
            lines.append(f"  📍 {place.address}")
        if place.phone:
            lines.append(f"  📞 {place.phone}")
    lines.append(f"\nВся карта: {_SITE}/map")
    await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())


async def try_map_keywords(db: AsyncSession, peer_id: int, text_lower: str) -> bool:
    """Справочник карты важнее ИИ для запросов «где аптека»."""
    if any(k in text_lower for k in ("гостиниц", "отель", "ночлег", "где жить", "проживан")):
        await reply_places(db, peer_id, category=PlaceCategory.HOTEL)
        return True
    if "аптек" in text_lower:
        await reply_places(db, peer_id, category=PlaceCategory.PHARMACY)
        return True
    if any(k in text_lower for k in ("магазин", "продукт", "пятёроч", "магнит", "супермаркет")):
        await reply_places(db, peer_id, categories=(PlaceCategory.SHOP, PlaceCategory.SUPERMARKET))
        return True
    if any(k in text_lower for k in ("кафе", "ресторан", "поесть")):
        await reply_places(db, peer_id, categories=(PlaceCategory.CAFE, PlaceCategory.RESTAURANT))
        return True
    if any(k in text_lower for k in ("банк", "банкомат", "сбер")):
        await reply_places(db, peer_id, category=PlaceCategory.BANK)
        return True
    if any(k in text_lower for k in ("больниц", "поликлин", "врач", "медиц")):
        await reply_places(db, peer_id, category=PlaceCategory.HOSPITAL)
        return True
    if any(k in text_lower for k in ("музей", "михайловск", "пушкин", "лавр", "монаст")):
        await reply_places(db, peer_id, category=PlaceCategory.CULTURE)
        return True
    if any(k in text_lower for k in ("такси", "извоз")):
        result = await db.execute(
            select(TaxiService).where(TaxiService.is_active.is_(True)).order_by(TaxiService.sort_order)
        )
        services = result.scalars().all()
        lines = ["🚕 Такси:\n"]
        for taxi in services:
            lines.append(f"• {taxi.name}: {taxi.phone}")
        lines.append(f"\n{_SITE}/map")
        await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())
        return True
    if any(k in text_lower for k in ("шиномонтаж", "шины", "колеса", "колёса")):
        await reply_places(db, peer_id, category=PlaceCategory.TYRE)
        return True
    if any(k in text_lower for k in ("азс", "заправка", "бензин")):
        await reply_places(db, peer_id, category=PlaceCategory.GAS)
        return True
    return False

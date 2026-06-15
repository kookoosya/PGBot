"""Вспомогательные функции ответов VK-бота и справочник карты."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus, PlaceCategory
from app.models.place import Place
from app.models.taxi import TaxiService
from app.services.site_urls import public_site_url
from app.services.vk.client import get_ai_keyboard, get_inline_links_keyboard, get_welcome_keyboard, send_message
from app.services.vk.context import VkRouteContext
from app.services.vk.bot import subscribe_peer

AI_EXAMPLES = (
    "• Напиши объявление про дрова\n"
    "• Что посмотреть в Пушкиногорье?\n"
    "• Идеи для дачи на лето\n"
    "• Как оформить жалобу в ЖКХ?"
)

ISSUE_STATUS_EMOJI = {
    IssueStatus.NEW: "🆕",
    IssueStatus.UNDER_REVIEW: "🔍",
    IssueStatus.ASSIGNED: "👤",
    IssueStatus.IN_PROGRESS: "🔧",
    IssueStatus.RESOLVED: "✅",
    IssueStatus.REJECTED: "❌",
}


async def send_welcome(ctx: VkRouteContext, message: str) -> None:
    await send_message(ctx.peer_id, message, keyboard=get_welcome_keyboard())


async def send_ai(ctx: VkRouteContext, message: str) -> None:
    await send_message(ctx.peer_id, message, keyboard=get_ai_keyboard())


async def send_with_site_links(peer_id: int, message: str, *paths: str) -> None:
    site = public_site_url()
    links = [(label, f"{site}{path}") for label, path in paths]
    kb = get_inline_links_keyboard(links) if links else get_welcome_keyboard()
    await send_message(peer_id, message, keyboard=kb)


async def subscribe_and_reply(ctx: VkRouteContext, preset: str) -> None:
    msg = await subscribe_peer(ctx.db, ctx.peer_id, preset)
    await send_welcome(ctx, msg)


async def start_flow_message(ctx: VkRouteContext, message: str) -> None:
    await send_welcome(ctx, message)


def format_taxi_lines(services: list[TaxiService], *, header: str, empty_line: str | None) -> str:
    lines = [header]
    if services:
        for taxi in services:
            lines.append(f"• {taxi.name}: {taxi.phone}")
    elif empty_line:
        lines.append(empty_line)
    lines.append(f"\n{public_site_url()}/map")
    return "\n".join(lines)


async def reply_taxi(db: AsyncSession, peer_id: int, *, header: str, empty_line: str | None = None) -> None:
    result = await db.execute(
        select(TaxiService).where(TaxiService.is_active.is_(True)).order_by(TaxiService.sort_order)
    )
    services = result.scalars().all()
    message = format_taxi_lines(services, header=header, empty_line=empty_line)
    await send_message(peer_id, message, keyboard=get_welcome_keyboard())


async def reply_places(
    db: AsyncSession,
    peer_id: int,
    *,
    category: PlaceCategory | None = None,
    categories: tuple[PlaceCategory, ...] | None = None,
    search: str | None = None,
) -> None:
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
            f"Пока не нашёл в справочнике. Откройте карту:\n{public_site_url()}/map",
            keyboard=get_welcome_keyboard(),
        )
        return
    lines = ["🗺 На карте посёлка:\n"]
    for p in places:
        lines.append(f"• {p.name}")
        if p.address:
            lines.append(f"  📍 {p.address}")
        if p.phone:
            lines.append(f"  📞 {p.phone}")
    lines.append(f"\nВся карта: {public_site_url()}/map")
    await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())


async def try_map_keywords(ctx: VkRouteContext) -> bool:
    """Справочник карты важнее ИИ для запросов «где аптека»."""
    text_lower = ctx.text_lower
    db = ctx.db
    peer_id = ctx.peer_id

    if any(k in text_lower for k in ("гостиниц", "отель", "ночлег", "где жить", "проживан")):
        await reply_places(db, peer_id, category=PlaceCategory.HOTEL)
        return True
    if "аптек" in text_lower:
        await reply_places(db, peer_id, category=PlaceCategory.PHARMACY)
        return True
    if any(k in text_lower for k in ("магазин", "продукт", "пятёроч", "магнит", "супермаркет")):
        await reply_places(
            db, peer_id,
            categories=(PlaceCategory.SHOP, PlaceCategory.SUPERMARKET),
        )
        return True
    if any(k in text_lower for k in ("кафе", "ресторан", "поесть")):
        await reply_places(
            db, peer_id,
            categories=(PlaceCategory.CAFE, PlaceCategory.RESTAURANT),
        )
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
        await reply_taxi(db, peer_id, header="🚕 Такси:\n")
        return True
    if any(k in text_lower for k in ("шиномонтаж", "шины", "колеса", "колёса")):
        await reply_places(db, peer_id, category=PlaceCategory.TYRE)
        return True
    if any(k in text_lower for k in ("азс", "заправка", "бензин")):
        await reply_places(db, peer_id, category=PlaceCategory.GAS)
        return True
    return False

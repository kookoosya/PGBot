"""Маршрутизация текстовых команд VK-бота (кнопки меню и ключевые слова)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.models.taxi import TaxiService
from app.services.vk import get_welcome_keyboard, send_message
from app.services.vk_ai_mode_store import discard_ai_mode
from app.services.vk_bot import format_ads_message, subscribe_peer, unsubscribe_peer
from app.services.vk_flows import (
    format_jobs_message,
    format_routes_message,
    start_classified_flow,
    start_map_report_flow,
    start_wish_flow,
)
from app.services.vk_messages import box, help_text
from app.services.vk_webhook.sender import send_with_site_links

settings = get_settings()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")


async def reply_my_issues(db: AsyncSession, peer_id: int) -> None:
    """Список обращений пользователя по vk_peer_id."""
    result = await db.execute(
        select(Issue)
        .options(selectinload(Issue.ai_analysis))
        .where(Issue.vk_peer_id == peer_id, Issue.parent_issue_id.is_(None))
        .order_by(Issue.created_at.desc())
        .limit(10)
    )
    issues = result.scalars().all()
    if not issues:
        await send_message(
            peer_id,
            "📋 Обращений пока нет. Опишите проблему — приму заявку!",
            keyboard=get_welcome_keyboard(),
        )
        return

    status_emoji = {
        IssueStatus.NEW: "🆕",
        IssueStatus.UNDER_REVIEW: "🔍",
        IssueStatus.ASSIGNED: "👤",
        IssueStatus.IN_PROGRESS: "🔧",
        IssueStatus.RESOLVED: "✅",
        IssueStatus.REJECTED: "❌",
    }
    lines = ["📋 Ваши обращения:\n"]
    for issue in issues:
        emoji = status_emoji.get(issue.status, "📋")
        summary = issue.ai_analysis.summary if issue.ai_analysis else issue.description[:50]
        lines.append(f"{emoji} #{issue.id} — {summary}")
    await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())


async def try_route_command(
    db: AsyncSession,
    peer_id: int,
    text_lower: str,
) -> bool:
    """Попытаться обработать известную команду. True — команда распознана."""
    if text_lower in ("📋 объявления", "объявления", "объявление", "доска"):
        await discard_ai_mode(db, peer_id)
        msg = await format_ads_message(db)
        await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("🛠 услуги", "услуги", "мастера", "огород", "дрова"):
        await discard_ai_mode(db, peer_id)
        await send_message(
            peer_id,
            box(
                "Услуги посёлка",
                f"Огород, дрова, покос, мастера с записью:\n{_SITE}/services\n\n"
                f"📋 Объявления соседей:\n{_SITE}/classifieds\n\n"
                "✨ Всё бесплатно",
            ),
            keyboard=get_welcome_keyboard(),
        )
        return True

    if text_lower in ("🔔 подписаться", "подписаться", "подписка", "подписка все"):
        msg = await subscribe_peer(db, peer_id, "all")
        await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("подписка работа", "подписка вакансии", "🔔 работа"):
        msg = await subscribe_peer(db, peer_id, "jobs")
        await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("подписка дрова", "подписка услуги"):
        preset = "firewood" if "дрова" in text_lower else "services"
        msg = await subscribe_peer(db, peer_id, preset)
        await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("🔕 отписаться", "отписаться"):
        msg = await unsubscribe_peer(db, peer_id)
        await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("💼 работа", "работа", "вакансии", "вакансия", "подработка"):
        await discard_ai_mode(db, peer_id)
        msg = await format_jobs_message(db)
        await send_with_site_links(peer_id, msg, ("💼 Вакансии", "/jobs"))
        return True

    if text_lower.startswith("маршруты ") and text_lower.split()[-1].isdigit():
        page = int(text_lower.split()[-1]) - 1
        await send_with_site_links(peer_id, format_routes_message(page), ("🗺 На карте", "/map"))
        return True

    if text_lower in ("🛤 маршруты", "маршруты", "маршрут", "куда сходить", "экскурсия"):
        await discard_ai_mode(db, peer_id)
        await send_with_site_links(peer_id, format_routes_message(0), ("🗺 На карте", "/map"))
        return True

    if text_lower in ("🗺 ошибка карты", "ошибка карты", "ошибка на карте", "карта ошибка"):
        await discard_ai_mode(db, peer_id)
        await send_message(peer_id, await start_map_report_flow(db, peer_id), keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("➕ объявление", "подать объявление", "добавить объявление", "разместить объявление"):
        await discard_ai_mode(db, peer_id)
        await send_message(peer_id, await start_classified_flow(db, peer_id), keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("вакансия работа",) or text_lower == "вакансию":
        await discard_ai_mode(db, peer_id)
        msg = await start_classified_flow(db, peer_id, jobs=True)
        await send_message(peer_id, msg, keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("💡 пожелания", "пожелания", "предложения", "идея для сайта"):
        await discard_ai_mode(db, peer_id)
        await send_message(peer_id, await start_wish_flow(db, peer_id), keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("🚕 такси", "такси"):
        result = await db.execute(
            select(TaxiService).where(TaxiService.is_active.is_(True)).order_by(TaxiService.sort_order)
        )
        services = result.scalars().all()
        lines = ["🚕 Такси посёлка:\n"]
        if services:
            for taxi in services:
                lines.append(f"• {taxi.name}: {taxi.phone}")
        else:
            lines.append("Справочник обновляется. Напишите «аптека» или откройте карту.")
        lines.append(f"\n{_SITE}/map")
        await send_message(peer_id, "\n".join(lines), keyboard=get_welcome_keyboard())
        return True

    if text_lower in ("⚠️ жалобы", "жалобы", "обращения", "жалоба"):
        await discard_ai_mode(db, peer_id)
        await send_message(
            peer_id,
            box(
                "Жалобы жителей",
                f"Форма на сайте: {_SITE}/complaints\n\n"
                "Или опишите проблему прямо здесь — примем заявку.\n"
                "«Мои обращения» — статус ваших заявок.",
            ),
            keyboard=get_welcome_keyboard(),
        )
        return True

    if text_lower in ("📝 регистрация", "регистрация", "зарегистрироваться"):
        await discard_ai_mode(db, peer_id)
        await send_message(
            peer_id,
            box(
                "Регистрация",
                f"{_SITE}/register\n\n" "🏠 Житель\n🏢 Организация\n" "🏛 Администрация / ЖКХ\n💇 Мастер услуг",
            ),
            keyboard=get_welcome_keyboard(),
        )
        return True

    if text_lower in ("🌐 сайт", "сайт"):
        await send_message(
            peer_id,
            box("Портал посёлка", f"{_SITE}\n\nГлавная · Карта · Объявления · Услуги · Жалобы · ИИ"),
            keyboard=get_welcome_keyboard(),
        )
        return True

    if text_lower in ("🗺 карта", "карта"):
        await send_message(
            peer_id,
            box(
                "Карта посёлка",
                f"{_SITE}/map\n\n"
                "Магазины, аптеки, кафе, АЗС, гостиницы, маршруты.\n"
                "Напишите: «аптека», «магазин», «заправка», «музей»",
            ),
            keyboard=get_welcome_keyboard(),
        )
        return True

    if text_lower in ("📋 мои обращения", "мои обращения"):
        await reply_my_issues(db, peer_id)
        return True

    if text_lower in ("ℹ️ помощь", "помощь"):
        await send_message(peer_id, help_text(), keyboard=get_welcome_keyboard())
        return True

    return False

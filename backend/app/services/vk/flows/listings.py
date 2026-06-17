"""VK listings: jobs and map routes."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedPaymentStatus, JOB_CLASSIFIED_CATEGORIES
from app.services.map_routes import get_map_routes
from app.services.site_urls import public_site_url


async def format_jobs_message(db: AsyncSession, limit: int = 6) -> str:
    result = await db.execute(
        select(ClassifiedAd)
        .where(
            ClassifiedAd.is_active.is_(True),
            ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
            ClassifiedAd.category.in_(JOB_CLASSIFIED_CATEGORIES),
        )
        .order_by(ClassifiedAd.created_at.desc())
        .limit(limit)
    )
    ads = list(result.scalars().all())
    if not ads:
        return (
            "💼 Вакансий пока нет.\n\n"
            f"Разместите первую — кнопка «➕ Объявление» или:\n{public_site_url()}/jobs"
        )
    lines = [f"💼 Работа и вакансии ({len(ads)}):\n"]
    for ad in ads:
        cat = CLASSIFIED_LABELS.get(ad.category, ad.category)
        pay = f" · {ad.price} {ad.price_unit or '₽'}" if ad.price else ""
        lines.append(f"• [{cat}] {ad.title}{pay}")
        lines.append(f"  {ad.description[:80]}{'…' if len(ad.description) > 80 else ''}")
        lines.append(f"  📞 {ad.phone}")
    lines.append(f"\nВсе вакансии: {public_site_url()}/jobs")
    lines.append("Разместить: «➕ Объявление»")
    return "\n".join(lines)


def format_routes_message(page: int = 0) -> str:
    routes = get_map_routes()
    per_page = 5
    start = page * per_page
    chunk = routes[start : start + per_page]
    lines = [f"🛤 Маршруты ({len(routes)} всего):\n"]
    for i, route in enumerate(chunk, start + 1):
        lines.append(f"{i}. {route['title']} — {route['duration']}")
        lines.append(f"   {route['description']}")
    if start + per_page < len(routes):
        lines.append(f"\nЕщё: напишите «маршруты {page + 2}»")
    lines.append(f"\nНа карте с линией маршрута:\n{public_site_url()}/map")
    return "\n".join(lines)

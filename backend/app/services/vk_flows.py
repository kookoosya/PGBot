"""Многошаговые сценарии VK-бота: объявления, пожелания."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import (
    CLASSIFIED_LABELS,
    ClassifiedCategory,
    ClassifiedPaymentStatus,
    JOB_CLASSIFIED_CATEGORIES,
)
from app.models.site_feedback import SiteFeedback
from app.services.classified_antifraud import (
    check_phone_rate_limit,
    check_recent_duplicate,
    find_scam_phrase,
    validate_phone,
)
from app.services.map_routes import get_map_routes
from app.services.notifications import notify_owner
from app.services.vk_messages import box

logger = logging.getLogger(__name__)
settings = get_settings()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")

# peer_id -> {kind, step, data}
_flows: dict[int, dict[str, Any]] = {}


def clear_flow(peer_id: int) -> None:
    _flows.pop(peer_id, None)


def get_flow(peer_id: int) -> dict[str, Any] | None:
    return _flows.get(peer_id)


def start_classified_flow(peer_id: int, *, jobs: bool = False) -> str:
    _flows[peer_id] = {
        "kind": "classified",
        "step": "title",
        "data": {"category": ClassifiedCategory.JOB if jobs else ClassifiedCategory.OTHER},
    }
    hint = "вакансию" if jobs else "объявление"
    return box(
        "Новое объявление",
        f"Размещение бесплатно, без регистрации.\n"
        f"Шаг 1 из 4 — напишите заголовок {hint}.\n\n"
        "«Отмена» — выйти.",
    )


def start_wish_flow(peer_id: int) -> str:
    _flows[peer_id] = {"kind": "wish", "step": "message", "data": {}}
    return box(
        "Пожелание",
        "Напишите идею или пожелание для портала — что улучшить, что добавить.\n\n"
        "«Отмена» — выйти.",
    )


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
            f"Разместите первую — кнопка «➕ Объявление» или:\n{_SITE}/classifieds?jobs=1"
        )
    lines = [f"💼 Работа и вакансии ({len(ads)}):\n"]
    for ad in ads:
        cat = CLASSIFIED_LABELS.get(ad.category, ad.category)
        pay = f" · {ad.price} {ad.price_unit or '₽'}" if ad.price else ""
        lines.append(f"• [{cat}] {ad.title}{pay}")
        lines.append(f"  {ad.description[:80]}{'…' if len(ad.description) > 80 else ''}")
        lines.append(f"  📞 {ad.phone}")
    lines.append(f"\nВсе вакансии: {_SITE}/classifieds?jobs=1")
    lines.append("Разместить: «➕ Объявление»")
    return "\n".join(lines)


def format_routes_message() -> str:
    routes = get_map_routes()
    lines = ["🛤 Туристические маршруты:\n"]
    for r in routes:
        lines.append(f"• {r['title']} ({r['duration']})")
        lines.append(f"  {r['description']}")
        for i, stop in enumerate(r["stops"][:3], 1):
            lines.append(f"  {i}. {stop['name']}")
    lines.append(f"\nМаршруты на карте: {_SITE}/map")
    return "\n".join(lines)


async def handle_flow_message(
    db: AsyncSession,
    peer_id: int,
    from_id: int,
    text: str,
) -> str | None:
    """Обработать сообщение в активном сценарии. None — сценарий не активен."""
    flow = _flows.get(peer_id)
    if not flow:
        return None

    if text.lower().strip() in ("отмена", "стоп", "меню", "🏠 меню"):
        clear_flow(peer_id)
        return "Отменено. Напишите «меню»."

    kind = flow["kind"]
    if kind == "wish":
        msg = text.strip()
        if len(msg) < 5:
            return "Слишком коротко. Опишите пожелание подробнее или «отмена»."
        row = SiteFeedback(
            message=msg,
            contact=f"vk:{from_id}",
            page="vk-bot",
            visitor_key=f"vk_{from_id}",
        )
        db.add(row)
        await db.flush()
        clear_flow(peer_id)
        return box(
            "Спасибо!",
            "Пожелание принято. Учтём при развитии портала.\n\n"
            f"Ещё идеи — кнопка «💡 Пожелания» или {_SITE}/wishes",
        )

    if kind == "classified":
        data = flow["data"]
        step = flow["step"]

        if step == "title":
            title = text.strip()
            if len(title) < 5:
                return "Заголовок от 5 символов. Или «отмена»."
            data["title"] = title
            flow["step"] = "description"
            return "Шаг 2 — опишите подробнее (от 10 символов):"

        if step == "description":
            desc = text.strip()
            if len(desc) < 10:
                return "Описание от 10 символов. Или «отмена»."
            data["description"] = desc
            flow["step"] = "phone"
            return "Шаг 3 — телефон для связи (+7…):"

        if step == "phone":
            phone = text.strip()
            err = validate_phone(phone)
            if err:
                return f"{err}\nИли «отмена»."
            data["phone"] = phone
            flow["step"] = "name"
            return "Шаг 4 — как к вам обращаться (имя):"

        if step == "name":
            name = text.strip()
            if len(name) < 2:
                return "Имя от 2 символов. Или «отмена»."
            data["author_name"] = name

            scam = find_scam_phrase(f"{data['title']} {data['description']}")
            if scam:
                clear_flow(peer_id)
                return "Текст похож на мошенничество. Уберите предоплату и попробуйте снова."

            rate_err = await check_phone_rate_limit(db, data["phone"])
            if rate_err:
                clear_flow(peer_id)
                return rate_err

            dup_err = await check_recent_duplicate(db, data["phone"], data["title"])
            if dup_err:
                clear_flow(peer_id)
                return dup_err

            ad = ClassifiedAd(
                category=data.get("category", ClassifiedCategory.OTHER),
                title=data["title"],
                description=data["description"],
                phone=data["phone"],
                author_name=name,
                vk_id=from_id,
                is_active=False,
                payment_status=ClassifiedPaymentStatus.PENDING,
                placement_fee=0,
            )
            db.add(ad)
            await db.flush()
            clear_flow(peer_id)

            cat_label = CLASSIFIED_LABELS.get(ad.category, ad.category)
            await notify_owner(
                "📢 ОБЪЯВЛЕНИЕ ИЗ VK\n\n"
                f"#{ad.id} · {cat_label}\n"
                f"«{ad.title}»\n"
                f"{ad.description[:200]}\n\n"
                f"👤 {name}\n📞 {data['phone']}\n\n"
                f"Модерация: {_SITE}/admin/classifieds"
            )
            return box(
                "Принято!",
                "Объявление на модерации — появится на портале и в VK после проверки.\n\n"
                f"Статус: {_SITE}/classifieds",
            )

    return None

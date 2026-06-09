"""Многошаговые сценарии VK-бота: объявления, пожелания."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.classified import ClassifiedAd
from app.models.enums import (
    CLASSIFIED_LABELS,
    JOB_CLASSIFIED_CATEGORIES,
    MAP_REPORT_LABELS,
    ClassifiedCategory,
    ClassifiedPaymentStatus,
    IssueCategory,
    IssueStatus,
    Priority,
    ShopComplaintType,
)
from app.models.issue import Issue
from app.models.place import Place, PlaceComplaint
from app.models.site_feedback import SiteFeedback
from app.services.classified_antifraud import (
    check_phone_rate_limit,
    check_recent_duplicate,
    find_scam_phrase,
    validate_phone,
)
from app.services.map_routes import get_map_routes
from app.services.notifications import notify_owner
from app.services.vk_flow_store import clear_flow, get_flow, save_flow
from app.services.vk_messages import box

logger = logging.getLogger(__name__)
settings = get_settings()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")


async def start_classified_flow(db: AsyncSession, peer_id: int, *, jobs: bool = False) -> str:
    flow = {
        "kind": "classified",
        "step": "title",
        "data": {"category": ClassifiedCategory.JOB_TOURISM if jobs else ClassifiedCategory.OTHER},
    }
    await save_flow(db, peer_id, flow)
    hint = "вакансию" if jobs else "объявление"
    return box(
        "Новое объявление",
        f"Размещение бесплатно, без регистрации.\n" f"Шаг 1 из 4 — напишите заголовок {hint}.\n\n" "«Отмена» — выйти.",
    )


async def start_wish_flow(db: AsyncSession, peer_id: int) -> str:
    await save_flow(db, peer_id, {"kind": "wish", "step": "message", "data": {}})
    return box(
        "Пожелание",
        "Напишите идею или пожелание для портала — что улучшить, что добавить.\n\n" "«Отмена» — выйти.",
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
        return "💼 Вакансий пока нет.\n\n" f"Разместите первую — кнопка «➕ Объявление» или:\n{_SITE}/jobs"
    lines = [f"💼 Работа и вакансии ({len(ads)}):\n"]
    for ad in ads:
        cat = CLASSIFIED_LABELS.get(ad.category, ad.category)
        pay = f" · {ad.price} {ad.price_unit or '₽'}" if ad.price else ""
        lines.append(f"• [{cat}] {ad.title}{pay}")
        lines.append(f"  {ad.description[:80]}{'…' if len(ad.description) > 80 else ''}")
        lines.append(f"  📞 {ad.phone}")
    lines.append(f"\nВсе вакансии: {_SITE}/jobs")
    lines.append("Разместить: «➕ Объявление»")
    return "\n".join(lines)


def format_routes_message(page: int = 0) -> str:
    routes = get_map_routes()
    per_page = 5
    start = page * per_page
    chunk = routes[start : start + per_page]
    lines = [f"🛤 Маршруты ({len(routes)} всего):\n"]
    for i, r in enumerate(chunk, start + 1):
        lines.append(f"{i}. {r['title']} — {r['duration']}")
        lines.append(f"   {r['description']}")
    if start + per_page < len(routes):
        lines.append(f"\nЕщё: напишите «маршруты {page + 2}»")
    lines.append(f"\nНа карте с линией маршрута:\n{_SITE}/map")
    return "\n".join(lines)


MAP_REPORT_TYPES = [
    ShopComplaintType.MAP_WRONG_HOURS,
    ShopComplaintType.MAP_WRONG_PHONE,
    ShopComplaintType.MAP_CLOSED,
    ShopComplaintType.MAP_WRONG_ADDRESS,
    ShopComplaintType.MAP_OTHER,
]


async def start_map_report_flow(db: AsyncSession, peer_id: int) -> str:
    await save_flow(db, peer_id, {"kind": "map_report", "step": "search", "data": {}})
    return box(
        "Ошибка на карте",
        "Напишите название места или улицу — найду в справочнике.\n\n" "«Отмена» — выйти.",
    )


async def _search_places_for_report(db: AsyncSession, query: str) -> list[Place]:
    q = query.strip()
    if len(q) < 2:
        return []
    result = await db.execute(
        select(Place)
        .where(
            Place.is_active.is_(True),
            Place.name.ilike(f"%{q}%") | Place.address.ilike(f"%{q}%"),
        )
        .order_by(Place.name)
        .limit(6)
    )
    return list(result.scalars().all())


async def _submit_map_report(
    db: AsyncSession,
    place: Place,
    report_type: ShopComplaintType,
    description: str,
    peer_id: int,
) -> str:
    type_label = MAP_REPORT_LABELS.get(report_type, report_type.value)
    complaint = PlaceComplaint(
        place_id=place.id,
        complaint_type=report_type,
        description=description,
        author_name=f"VK #{peer_id}",
    )
    db.add(complaint)
    place.complaint_count += 1

    issue_desc = f"Ошибка на карте: {place.name} ({place.address or ''})\n" f"Тип: {type_label}\n{description}"
    issue = Issue(
        title=f"Карта: {place.name}",
        description=issue_desc,
        status=IssueStatus.NEW,
        category=IssueCategory.OTHER,
        priority=Priority.MEDIUM,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        vk_peer_id=peer_id,
    )
    db.add(issue)
    await db.flush()
    complaint.issue_id = issue.id

    await notify_owner(
        f"🗺 ОШИБКА НА КАРТЕ (VK)\n\n" f"«{place.name}» — {place.address or '—'}\n" f"{type_label}\n{description[:300]}"
    )
    return box(
        "Спасибо!",
        f"Сообщение об ошибке принято.\nМесто: {place.name}\nПроверим и обновим карту.",
    )


async def handle_flow_message(
    db: AsyncSession,
    peer_id: int,
    from_id: int,
    text: str,
) -> str | None:
    """Обработать сообщение в активном сценарии. None — сценарий не активен."""
    flow = await get_flow(db, peer_id)
    if not flow:
        return None

    if text.lower().strip() in ("отмена", "стоп", "меню", "🏠 меню"):
        await clear_flow(db, peer_id)
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
        await clear_flow(db, peer_id)
        return box(
            "Спасибо!",
            "Пожелание принято. Учтём при развитии портала.\n\n" f"Ещё идеи — кнопка «💡 Пожелания» или {_SITE}/wishes",
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
            await save_flow(db, peer_id, flow)
            return "Шаг 2 — опишите подробнее (от 10 символов):"

        if step == "description":
            desc = text.strip()
            if len(desc) < 10:
                return "Описание от 10 символов. Или «отмена»."
            data["description"] = desc
            flow["step"] = "phone"
            await save_flow(db, peer_id, flow)
            return "Шаг 3 — телефон для связи (+7…):"

        if step == "phone":
            phone = text.strip()
            err = validate_phone(phone)
            if err:
                return f"{err}\nИли «отмена»."
            data["phone"] = phone
            flow["step"] = "name"
            await save_flow(db, peer_id, flow)
            return "Шаг 4 — как к вам обращаться (имя):"

        if step == "name":
            name = text.strip()
            if len(name) < 2:
                return "Имя от 2 символов. Или «отмена»."
            data["author_name"] = name

            scam = find_scam_phrase(f"{data['title']} {data['description']}")
            if scam:
                await clear_flow(db, peer_id)
                return "Текст похож на мошенничество. Уберите предоплату и попробуйте снова."

            rate_err = await check_phone_rate_limit(db, data["phone"])
            if rate_err:
                await clear_flow(db, peer_id)
                return rate_err

            dup_err = await check_recent_duplicate(db, data["phone"], data["title"])
            if dup_err:
                await clear_flow(db, peer_id)
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
            await clear_flow(db, peer_id)

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

    if kind == "map_report":
        data = flow["data"]
        step = flow["step"]

        if step == "search":
            places = await _search_places_for_report(db, text)
            if not places:
                return "Не нашёл. Уточните название или «отмена»."
            data["places"] = [{"id": p.id, "name": p.name, "address": p.address or ""} for p in places]
            flow["step"] = "pick"
            await save_flow(db, peer_id, flow)
            lines = ["Выберите номер места:\n"]
            for i, p in enumerate(places, 1):
                lines.append(f"{i}. {p.name}")
                if p.address:
                    lines.append(f"   📍 {p.address}")
            return "\n".join(lines)

        if step == "pick":
            try:
                idx = int(text.strip()) - 1
                picked = data["places"][idx]
            except (ValueError, IndexError, KeyError):
                return "Напишите номер из списка (1–6) или «отмена»."
            data["place_id"] = picked["id"]
            data["place_name"] = picked["name"]
            flow["step"] = "type"
            await save_flow(db, peer_id, flow)
            lines = ["Тип ошибки — напишите номер:\n"]
            for i, t in enumerate(MAP_REPORT_TYPES, 1):
                lines.append(f"{i}. {MAP_REPORT_LABELS[t]}")
            return "\n".join(lines)

        if step == "type":
            try:
                tidx = int(text.strip()) - 1
                report_type = MAP_REPORT_TYPES[tidx]
            except (ValueError, IndexError):
                return "Напишите номер типа (1–5) или «отмена»."
            data["report_type"] = report_type.value
            flow["step"] = "description"
            await save_flow(db, peer_id, flow)
            return f"Опишите ошибку для «{data['place_name']}» (от 10 символов):"

        if step == "description":
            desc = text.strip()
            if len(desc) < 10:
                return "Описание от 10 символов. Или «отмена»."
            result = await db.execute(select(Place).where(Place.id == data["place_id"]))
            place = result.scalar_one_or_none()
            if not place:
                await clear_flow(db, peer_id)
                return "Место не найдено. Начните заново."
            report_type = ShopComplaintType(data["report_type"])
            msg = await _submit_map_report(db, place, report_type, desc, peer_id)
            await clear_flow(db, peer_id)
            return msg

    return None

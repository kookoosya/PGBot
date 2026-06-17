"""VK flow: map place error reports."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    MAP_REPORT_LABELS,
    IssueCategory,
    IssueStatus,
    Priority,
    ShopComplaintType,
)
from app.models.issue import Issue
from app.models.place import Place, PlaceComplaint
from app.services.notifications import notify_owner
from app.services.vk.flow_store import clear_flow as clear_flow_state
from app.services.vk.flow_store import save_flow
from app.services.vk.messages import box

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
        "Напишите название места или улицу — найду в справочнике.\n\n"
        "«Отмена» — выйти.",
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

    issue_desc = (
        f"Ошибка на карте: {place.name} ({place.address or ''})\n"
        f"Тип: {type_label}\n{description}"
    )
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
        f"🗺 ОШИБКА НА КАРТЕ (VK)\n\n"
        f"«{place.name}» — {place.address or '—'}\n"
        f"{type_label}\n{description[:300]}"
    )
    return box(
        "Спасибо!",
        f"Сообщение об ошибке принято.\nМесто: {place.name}\nПроверим и обновим карту.",
    )


async def handle_map_report_flow(
    db: AsyncSession,
    peer_id: int,
    text: str,
    flow: dict[str, Any],
) -> str:
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
        for i, place in enumerate(places, 1):
            lines.append(f"{i}. {place.name}")
            if place.address:
                lines.append(f"   📍 {place.address}")
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
        for i, report_type in enumerate(MAP_REPORT_TYPES, 1):
            lines.append(f"{i}. {MAP_REPORT_LABELS[report_type]}")
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
            await clear_flow_state(db, peer_id)
            return "Место не найдено. Начните заново."
        report_type = ShopComplaintType(data["report_type"])
        msg = await _submit_map_report(db, place, report_type, desc, peer_id)
        await clear_flow_state(db, peer_id)
        return msg

    return "Неизвестный шаг. Напишите «отмена»."

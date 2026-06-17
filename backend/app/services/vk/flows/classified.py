"""VK flow: classified ad creation."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.portal_copy import CLASSIFIED_SUBMITTED_VK, LINK_CLASSIFIEDS, LINK_SUBMIT_CLASSIFIED
from app.models.enums import ClassifiedCategory
from app.services.classified import ClassifiedValidationError, create_classified_ad_from_vk
from app.services.classified_antifraud import validate_phone
from app.services.site_urls import public_site_url
from app.services.vk.client import get_inline_links_keyboard, send_message
from app.services.vk.flow_store import clear_flow as clear_flow_state
from app.services.vk.flow_store import save_flow
from app.services.vk.messages import box


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
        f"Размещение бесплатно, без регистрации.\n"
        f"Шаг 1 из 4 — напишите заголовок {hint}.\n\n"
        "«Отмена» — выйти.",
    )


async def handle_classified_flow(
    db: AsyncSession,
    peer_id: int,
    from_id: int,
    text: str,
    flow: dict[str, Any],
) -> str | None:
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

        try:
            await create_classified_ad_from_vk(
                db,
                from_id=from_id,
                category=data.get("category", ClassifiedCategory.OTHER),
                title=data["title"],
                description=data["description"],
                phone=data["phone"],
                author_name=name,
            )
        except ClassifiedValidationError as exc:
            await clear_flow_state(db, peer_id)
            return str(exc)

        await clear_flow_state(db, peer_id)
        msg = box("Принято!", CLASSIFIED_SUBMITTED_VK)
        await send_message(
            peer_id,
            msg,
            keyboard=get_inline_links_keyboard([
                (LINK_CLASSIFIEDS, f"{public_site_url()}/classifieds"),
                (LINK_SUBMIT_CLASSIFIED, f"{public_site_url()}/classifieds?new=1"),
            ]),
        )
        return None

    return None

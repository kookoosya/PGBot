"""Персистентное хранилище многошаговых сценариев VK-бота."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClassifiedCategory
from app.models.vk_flow_state import VkFlowState


def _prepare_data_for_db(data: dict[str, Any]) -> dict[str, Any]:
    """Сериализуем enum-значения в data перед записью в JSON."""
    out = dict(data)
    category = out.get("category")
    if isinstance(category, ClassifiedCategory):
        out["category"] = category.value
    return out


def _restore_data_from_db(data: dict[str, Any]) -> dict[str, Any]:
    """Восстанавливаем enum-значения после чтения из JSON."""
    out = dict(data)
    category = out.get("category")
    if isinstance(category, str):
        try:
            out["category"] = ClassifiedCategory(category)
        except ValueError:
            out["category"] = ClassifiedCategory.OTHER
    return out


async def get_flow(db: AsyncSession, peer_id: int) -> dict[str, Any] | None:
    """Вернуть активный flow для peer_id или None, если сценарий не начат."""
    result = await db.execute(select(VkFlowState).where(VkFlowState.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if not row:
        return None
    try:
        data = json.loads(row.data or "{}")
        if not isinstance(data, dict):
            data = {}
    except json.JSONDecodeError:
        data = {}
    return {
        "kind": row.kind,
        "step": row.step,
        "data": _restore_data_from_db(data),
    }


async def save_flow(db: AsyncSession, peer_id: int, flow: dict[str, Any]) -> None:
    """Сохранить или обновить состояние flow для peer_id."""
    kind = str(flow["kind"])
    step = str(flow["step"])
    data = flow.get("data", {})
    if not isinstance(data, dict):
        data = {}
    payload = json.dumps(_prepare_data_for_db(data), ensure_ascii=False)

    result = await db.execute(select(VkFlowState).where(VkFlowState.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row:
        row.kind = kind
        row.step = step
        row.data = payload
    else:
        db.add(
            VkFlowState(
                peer_id=peer_id,
                kind=kind,
                step=step,
                data=payload,
            )
        )
    await db.flush()


async def clear_flow(db: AsyncSession, peer_id: int) -> None:
    """Удалить активный flow для peer_id."""
    result = await db.execute(select(VkFlowState).where(VkFlowState.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.flush()


async def get_active_flows(db: AsyncSession) -> list[int]:
    """Список peer_id с активными сценариями (для отладки и мониторинга)."""
    result = await db.execute(select(VkFlowState.peer_id))
    return [int(peer_id) for peer_id in result.scalars().all()]

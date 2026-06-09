"""Хранение состояния VK-сценариев в PostgreSQL (устойчиво к рестарту и нескольким workers)."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClassifiedCategory
from app.models.vk_flow_state import VkFlowState

logger = logging.getLogger(__name__)


def _enum_to_value(obj: Any) -> Any:
    if hasattr(obj, "value"):
        return obj.value
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _serialize_flow(flow: dict[str, Any]) -> tuple[str, str, str]:
    """Разложить flow на колонки таблицы."""
    return flow["kind"], flow["step"], json.dumps(flow.get("data") or {}, default=_enum_to_value, ensure_ascii=False)


def _deserialize_flow(kind: str, step: str, data_json: str) -> dict[str, Any]:
    """Собрать flow из строк БД, восстановив enum-поля."""
    try:
        data = json.loads(data_json) if data_json else {}
    except json.JSONDecodeError:
        logger.warning("Invalid vk flow JSON for kind=%s step=%s", kind, step)
        data = {}

    if kind == "classified" and "category" in data:
        try:
            data["category"] = ClassifiedCategory(data["category"])
        except ValueError:
            data["category"] = ClassifiedCategory.OTHER

    return {"kind": kind, "step": step, "data": data}


async def get_flow(db: AsyncSession, peer_id: int) -> dict[str, Any] | None:
    result = await db.execute(select(VkFlowState).where(VkFlowState.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if not row:
        return None
    return _deserialize_flow(row.kind, row.step, row.data)


async def save_flow(db: AsyncSession, peer_id: int, flow: dict[str, Any]) -> None:
    kind, step, data_json = _serialize_flow(flow)
    result = await db.execute(select(VkFlowState).where(VkFlowState.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row:
        row.kind = kind
        row.step = step
        row.data = data_json
    else:
        db.add(VkFlowState(peer_id=peer_id, kind=kind, step=step, data=data_json))
    await db.flush()


async def clear_flow(db: AsyncSession, peer_id: int) -> None:
    result = await db.execute(select(VkFlowState).where(VkFlowState.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.flush()

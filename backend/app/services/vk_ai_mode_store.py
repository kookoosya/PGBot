"""Хранение флага ИИ-режима VK в PostgreSQL (устойчиво к рестарту и нескольким workers)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vk_ai_mode import VkAiMode


async def is_ai_mode(db: AsyncSession, peer_id: int) -> bool:
    result = await db.execute(select(VkAiMode.peer_id).where(VkAiMode.peer_id == peer_id))
    return result.scalar_one_or_none() is not None


async def enter_ai_mode(db: AsyncSession, peer_id: int) -> None:
    result = await db.execute(select(VkAiMode).where(VkAiMode.peer_id == peer_id))
    if result.scalar_one_or_none():
        return
    db.add(VkAiMode(peer_id=peer_id))
    await db.flush()


async def discard_ai_mode(db: AsyncSession, peer_id: int) -> None:
    result = await db.execute(select(VkAiMode).where(VkAiMode.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.flush()

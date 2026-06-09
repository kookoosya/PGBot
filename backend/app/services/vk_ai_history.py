"""История диалога ИИ в VK — сохраняется в БД."""

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vk_ai_session import VkAiSession

MAX_MESSAGES = 10


async def get_ai_history(db: AsyncSession, peer_id: int) -> list[dict]:
    result = await db.execute(select(VkAiSession).where(VkAiSession.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if not row or not row.messages:
        return []
    try:
        data = json.loads(row.messages)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


async def append_ai_turn(db: AsyncSession, peer_id: int, user_text: str, assistant_text: str) -> None:
    history = await get_ai_history(db, peer_id)
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": assistant_text})
    history = history[-MAX_MESSAGES:]
    payload = json.dumps(history, ensure_ascii=False)

    result = await db.execute(select(VkAiSession).where(VkAiSession.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row:
        row.messages = payload
    else:
        db.add(VkAiSession(peer_id=peer_id, messages=payload))
    await db.flush()


async def clear_ai_history(db: AsyncSession, peer_id: int) -> None:
    result = await db.execute(select(VkAiSession).where(VkAiSession.peer_id == peer_id))
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.flush()

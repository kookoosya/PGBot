"""Pool of Gemini API keys — rotation for paid users."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_provider_key import AIProviderKey
from app.services.ai_status import is_valid_gemini_key

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass(frozen=True, slots=True)
class GeminiKeyCandidate:
    key_id: int | None
    api_key: str
    source: str


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_env_gemini_keys() -> list[str]:
    from app.services.ai_status import env_gemini_keys

    return env_gemini_keys()


def mask_api_key(key: str) -> str:
    key = key.strip()
    if len(key) <= 8:
        return "••••"
    return f"{key[:4]}…{key[-4:]}"


async def list_gemini_key_rows(db: AsyncSession, *, include_inactive: bool = False) -> list[AIProviderKey]:
    query = select(AIProviderKey).where(AIProviderKey.provider == "gemini")
    if not include_inactive:
        query = query.where(AIProviderKey.is_active.is_(True))
    query = query.order_by(AIProviderKey.priority.asc(), AIProviderKey.use_count.asc(), AIProviderKey.id.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def count_active_gemini_keys(db: AsyncSession | None) -> int:
    db_keys = 0
    if db is not None:
        rows = await list_gemini_key_rows(db)
        db_keys = len(rows)
    env_keys = len(_parse_env_gemini_keys())
    return db_keys + env_keys


async def build_gemini_key_candidates(db: AsyncSession | None) -> list[GeminiKeyCandidate]:
    candidates: list[GeminiKeyCandidate] = []
    seen: set[str] = set()

    if db is not None:
        for row in await list_gemini_key_rows(db):
            key = row.api_key.strip()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(GeminiKeyCandidate(key_id=row.id, api_key=key, source="db"))

    for key in _parse_env_gemini_keys():
        if key in seen:
            continue
        seen.add(key)
        candidates.append(GeminiKeyCandidate(key_id=None, api_key=key, source="env"))

    return candidates


async def add_gemini_key(
    db: AsyncSession,
    *,
    api_key: str,
    label: str | None = None,
    priority: int = 100,
) -> AIProviderKey:
    key = api_key.strip()
    if not is_valid_gemini_key(key):
        raise ValueError("Некорректный ключ Gemini")

    existing = await db.execute(
        select(AIProviderKey).where(AIProviderKey.provider == "gemini", AIProviderKey.api_key == key)
    )
    row = existing.scalar_one_or_none()
    if row:
        row.is_active = True
        if label:
            row.label = label
        row.priority = priority
        await db.flush()
        return row

    row = AIProviderKey(
        provider="gemini",
        api_key=key,
        label=label,
        priority=priority,
        is_active=True,
    )
    db.add(row)
    await db.flush()
    return row


async def set_gemini_key_active(db: AsyncSession, key_id: int, *, active: bool) -> AIProviderKey | None:
    result = await db.execute(select(AIProviderKey).where(AIProviderKey.id == key_id))
    row = result.scalar_one_or_none()
    if not row:
        return None
    row.is_active = active
    await db.flush()
    return row


async def delete_gemini_key(db: AsyncSession, key_id: int) -> bool:
    result = await db.execute(select(AIProviderKey).where(AIProviderKey.id == key_id))
    row = result.scalar_one_or_none()
    if not row:
        return False
    await db.delete(row)
    await db.flush()
    return True


async def record_gemini_key_success(db: AsyncSession, key_id: int) -> None:
    result = await db.execute(select(AIProviderKey).where(AIProviderKey.id == key_id))
    row = result.scalar_one_or_none()
    if not row:
        return
    row.use_count += 1
    row.last_used_at = _now()
    await db.flush()


async def record_gemini_key_failure(db: AsyncSession, key_id: int, error: str) -> None:
    result = await db.execute(select(AIProviderKey).where(AIProviderKey.id == key_id))
    row = result.scalar_one_or_none()
    if not row:
        return
    row.error_count += 1
    row.last_error_at = _now()
    row.last_error = error[:500]
    await db.flush()


def _call_gemini_sync(
    api_key: str,
    message: str,
    history: list[dict] | None,
    model_id: str | None,
    system_prompt: str,
) -> str:
    genai.configure(api_key=api_key)
    model_name = model_id if model_id and model_id.startswith("gemini") else settings.GEMINI_MODEL
    model = genai.GenerativeModel(model_name, system_instruction=system_prompt)

    chat_history = []
    if history:
        for msg in history[-6:]:
            role = "user" if msg.get("role") == "user" else "model"
            chat_history.append({"role": role, "parts": [msg.get("content", "")]})

    chat = model.start_chat(history=chat_history)
    response = chat.send_message(message)
    return response.text.strip()


async def chat_with_gemini_pool(
    db: AsyncSession | None,
    message: str,
    history: list[dict] | None,
    model_id: str | None,
    system_prompt: str,
) -> str | None:
    candidates = await build_gemini_key_candidates(db)
    if not candidates:
        return None

    last_error: str | None = None
    for candidate in candidates:
        try:
            text = _call_gemini_sync(
                candidate.api_key,
                message,
                history,
                model_id,
                system_prompt,
            )
            if candidate.key_id is not None and db is not None:
                await record_gemini_key_success(db, candidate.key_id)
            return text
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Gemini key failed (%s): %s", candidate.source, exc)
            if candidate.key_id is not None and db is not None:
                await record_gemini_key_failure(db, candidate.key_id, last_error)
            continue

    if last_error:
        logger.warning("All Gemini keys failed: %s", last_error)
    return None

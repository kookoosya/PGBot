"""Automatic VK chat moderation — profanity, spam, warnings, bans."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.vk_moderation_config import (
    BAN_DURATION_DAYS,
    MAX_VIOLATION_WARNINGS,
    PROFANITY_PATTERNS,
    SPAM_CAPS_RATIO,
    SPAM_MAX_IDENTICAL_MESSAGES,
    SPAM_MAX_URLS,
    SPAM_MIN_LENGTH_FOR_CAPS,
    SPAM_REPEAT_WINDOW_SECONDS,
)
from app.models.vk_moderation import VkModerationLog, VkUserModeration
from app.services.vk import send_message

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://|www\.", re.I)
_PROFANITY_RES = [re.compile(p, re.I) for p in PROFANITY_PATTERNS]


@dataclass(frozen=True, slots=True)
class ModerationCheckResult:
    """Outcome of pre-message moderation check."""

    allowed: bool
    banned_until: datetime | None = None
    message: str | None = None


@dataclass(frozen=True, slots=True)
class ViolationResult:
    """Result after recording a violation."""

    warned: bool
    banned: bool
    warning_count: int
    user_message: str


def detect_profanity(text: str) -> bool:
    """Return True if text contains obscene language."""
    normalized = text.lower().replace("ё", "е")
    return any(pattern.search(normalized) for pattern in _PROFANITY_RES)


def detect_spam(text: str) -> bool:
    """Heuristic spam detection without ML."""
    stripped = text.strip()
    if len(stripped) < 4:
        return False
    if len(_URL_RE.findall(stripped)) >= SPAM_MAX_URLS:
        return True
    if len(stripped) >= SPAM_MIN_LENGTH_FOR_CAPS:
        letters = [c for c in stripped if c.isalpha()]
        if letters:
            upper_ratio = sum(1 for c in letters if c.isupper()) / len(letters)
            if upper_ratio >= SPAM_CAPS_RATIO:
                return True
    return False


async def _get_or_create_state(db: AsyncSession, vk_user_id: int, peer_id: int) -> VkUserModeration:
    result = await db.execute(select(VkUserModeration).where(VkUserModeration.vk_user_id == vk_user_id))
    state = result.scalar_one_or_none()
    if state:
        if state.peer_id != peer_id:
            state.peer_id = peer_id
        return state
    state = VkUserModeration(vk_user_id=vk_user_id, peer_id=peer_id, warning_count=0)
    db.add(state)
    await db.flush()
    return state


async def _recent_identical_count(
    db: AsyncSession,
    vk_user_id: int,
    text: str,
    *,
    window_seconds: int = SPAM_REPEAT_WINDOW_SECONDS,
) -> int:
    since = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
    excerpt = text.strip()[:500]
    result = await db.execute(
        select(VkModerationLog)
        .where(
            VkModerationLog.vk_user_id == vk_user_id,
            VkModerationLog.message_excerpt == excerpt,
            VkModerationLog.created_at >= since,
        )
    )
    return len(list(result.scalars().all()))


async def check_user_allowed(
    db: AsyncSession,
    vk_user_id: int,
    peer_id: int,
) -> ModerationCheckResult:
    """Return whether the user may send messages (not currently banned)."""
    state = await _get_or_create_state(db, vk_user_id, peer_id)
    now = datetime.now(timezone.utc)
    if state.banned_until and state.banned_until > now:
        until_label = state.banned_until.astimezone(timezone.utc).strftime("%d.%m.%Y %H:%M")
        return ModerationCheckResult(
            allowed=False,
            banned_until=state.banned_until,
            message=(
                f"⛔ Вы временно заблокированы до {until_label} UTC "
                f"за нарушения правил чата ({MAX_VIOLATION_WARNINGS} предупреждений).\n"
                "Напишите «помощь» после снятия блокировки."
            ),
        )
    if state.banned_until and state.banned_until <= now:
        state.banned_until = None
        await db.flush()
    return ModerationCheckResult(allowed=True)


async def evaluate_message_violation_for_user(
    db: AsyncSession,
    vk_user_id: int,
    text: str,
) -> str | None:
    """Return violation reason for a specific user message."""
    if detect_profanity(text):
        return "profanity"
    if detect_spam(text):
        return "spam"
    if await _recent_identical_count(db, vk_user_id, text) >= SPAM_MAX_IDENTICAL_MESSAGES - 1:
        return "spam_repeat"
    return None


async def record_violation(
    db: AsyncSession,
    vk_user_id: int,
    peer_id: int,
    text: str,
    reason: str,
) -> ViolationResult:
    """Increment warnings, optionally ban, log, and notify user."""
    state = await _get_or_create_state(db, vk_user_id, peer_id)
    now = datetime.now(timezone.utc)
    state.warning_count += 1
    state.last_violation_at = now

    banned = False
    action = "warn"
    if state.warning_count >= MAX_VIOLATION_WARNINGS:
        state.banned_until = now + timedelta(days=BAN_DURATION_DAYS)
        banned = True
        action = "ban"

    log = VkModerationLog(
        vk_user_id=vk_user_id,
        peer_id=peer_id,
        message_excerpt=text.strip()[:500],
        reason=reason,
        action=action,
        warning_number=state.warning_count,
    )
    db.add(log)
    await db.flush()

    reason_label = {"profanity": "нецензурная лексика", "spam": "спам", "spam_repeat": "повтор сообщений"}.get(
        reason, reason,
    )
    if banned:
        user_message = (
            f"⛔ Предупреждение {state.warning_count}/{MAX_VIOLATION_WARNINGS}: {reason_label}.\n"
            f"Достигнут лимит — блокировка на {BAN_DURATION_DAYS} дней."
        )
    else:
        remaining = MAX_VIOLATION_WARNINGS - state.warning_count
        user_message = (
            f"⚠️ Предупреждение {state.warning_count}/{MAX_VIOLATION_WARNINGS}: {reason_label}.\n"
            f"Осталось до блокировки: {remaining}. Пожалуйста, соблюдайте правила чата."
        )

    logger.info(
        "VK moderation %s user=%s warnings=%s reason=%s",
        action, vk_user_id, state.warning_count, reason,
    )
    return ViolationResult(
        warned=True,
        banned=banned,
        warning_count=state.warning_count,
        user_message=user_message,
    )


async def process_incoming_moderation(
    db: AsyncSession,
    vk_user_id: int,
    peer_id: int,
    text: str,
) -> ModerationCheckResult:
    """Full pipeline: ban check → violation scan → warn/ban."""
    check = await check_user_allowed(db, vk_user_id, peer_id)
    if not check.allowed:
        return check

    reason = await evaluate_message_violation_for_user(db, vk_user_id, text)
    if not reason:
        return ModerationCheckResult(allowed=True)

    result = await record_violation(db, vk_user_id, peer_id, text, reason)
    await send_message(peer_id, result.user_message)
    state = await _get_or_create_state(db, vk_user_id, peer_id)
    return ModerationCheckResult(
        allowed=False,
        banned_until=state.banned_until if result.banned else None,
        message=result.user_message,
    )


async def list_moderation_states(db: AsyncSession, *, limit: int = 100) -> list[VkUserModeration]:
    """Users with warnings or active bans."""
    result = await db.execute(
        select(VkUserModeration)
        .where((VkUserModeration.warning_count > 0) | VkUserModeration.banned_until.isnot(None))
        .order_by(desc(VkUserModeration.updated_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_moderation_logs(db: AsyncSession, *, limit: int = 100) -> list[VkModerationLog]:
    result = await db.execute(
        select(VkModerationLog).order_by(desc(VkModerationLog.created_at)).limit(limit)
    )
    return list(result.scalars().all())


async def unblock_vk_user(db: AsyncSession, vk_user_id: int) -> VkUserModeration | None:
    """Admin: clear ban and reset warnings."""
    result = await db.execute(select(VkUserModeration).where(VkUserModeration.vk_user_id == vk_user_id))
    state = result.scalar_one_or_none()
    if not state:
        return None
    state.banned_until = None
    state.warning_count = 0
    await db.flush()
    await send_message(
        state.peer_id,
        "✅ Блокировка снята администратором. Пожалуйста, соблюдайте правила чата.",
    )
    return state

"""Оркестрация обработки входящего message_new от VK."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.issue_processor import process_incoming_message
from app.services.vk import get_welcome_keyboard, get_welcome_message, send_message
from app.services.vk_ai_history import clear_ai_history
from app.services.vk_flow_store import clear_flow
from app.services.vk_flows import handle_flow_message
from app.services.vk_messages import box, looks_like_complaint
from app.services.vk_voice import extract_audio_url, transcribe_audio_url
from app.services.vk_webhook.ai_mode import discard_ai_mode, handle_ai_commands, try_ai_message
from app.services.vk_webhook.command_router import try_route_command
from app.services.vk_webhook.map_replies import try_map_keywords

logger = logging.getLogger(__name__)

MENU_TRIGGERS = frozenset(
    {
        "начать",
        "start",
        "привет",
        "здравствуйте",
        "hello",
        "меню",
        "🏠 меню",
        "главная",
        "🏠 главная",
    }
)


async def handle_menu_reset(db: AsyncSession, peer_id: int) -> None:
    """Сброс flows, ИИ-истории и возврат в главное меню."""
    discard_ai_mode(peer_id)
    await clear_flow(db, peer_id)
    await clear_ai_history(db, peer_id)
    await send_message(peer_id, get_welcome_message(), keyboard=get_welcome_keyboard())


async def handle_voice_message(
    peer_id: int,
    text: str,
    attachments: list[Any] | None,
) -> tuple[str, str] | None:
    """
    Распознать голосовое вложение.
    Возвращает (text, text_lower) или None, если голос не обработан.
    """
    audio_url = extract_audio_url(attachments or [])
    if not audio_url:
        return None

    transcribed = await transcribe_audio_url(audio_url)
    if transcribed:
        await send_message(peer_id, f"🎤 Распознано: «{transcribed[:200]}»")
        return transcribed, transcribed.lower()

    if not text.strip():
        await send_message(
            peer_id,
            "Не удалось распознать голосовое. Напишите текстом или повторите.",
            keyboard=get_welcome_keyboard(),
        )
    return None


async def handle_flow(db: AsyncSession, peer_id: int, from_id: int, text: str) -> bool:
    """Обработать активный многошаговый сценарий. True — сообщение обработано."""
    flow_reply = await handle_flow_message(db, peer_id, from_id, text)
    if not flow_reply:
        return False
    discard_ai_mode(peer_id)
    await send_message(peer_id, flow_reply, keyboard=get_welcome_keyboard())
    return True


async def handle_complaint(
    db: AsyncSession,
    parsed: dict[str, Any],
    peer_id: int,
    from_id: int,
    text: str,
) -> bool:
    """Принять жалобу или фото проблемы. True — обработано."""
    complaint_text = text.strip()
    if parsed.get("photos") and len(complaint_text) < 5:
        complaint_text = "Фото проблемы (VK)"

    if not looks_like_complaint(complaint_text) and not parsed.get("photos"):
        return False

    try:
        await process_incoming_message(
            db,
            text=complaint_text,
            vk_id=from_id,
            peer_id=peer_id,
            message_id=parsed.get("message_id"),
            photos=parsed.get("photos"),
        )
    except Exception as exc:
        logger.exception("Error processing VK message: %s", exc)
        await send_message(peer_id, "Ошибка. Напишите «помощь».", keyboard=get_welcome_keyboard())
    return True


async def send_unknown_message(peer_id: int) -> None:
    """Ответ, если сообщение не распознано."""
    await send_message(
        peer_id,
        box(
            "Не понял сообщение",
            "Выберите кнопку меню или:\n"
            "🤖 ИИ-помощник — любые вопросы\n"
            "⚠️ Жалобы — опишите проблему подробно\n\n"
            "«Меню» — вернуться к разделам",
        ),
        keyboard=get_welcome_keyboard(),
    )


async def handle_message_new(db: AsyncSession, parsed: dict[str, Any]) -> None:
    """Главный пайплайн обработки message_new."""
    text = parsed["text"]
    from_id = parsed["from_id"]
    peer_id = parsed["peer_id"]
    text_lower = text.lower()

    if text_lower in MENU_TRIGGERS:
        await handle_menu_reset(db, peer_id)
        return

    voice_result = await handle_voice_message(peer_id, text, parsed.get("attachments"))
    if voice_result is None and extract_audio_url(parsed.get("attachments") or []) and not text.strip():
        return
    if voice_result:
        text, text_lower = voice_result

    if await handle_flow(db, peer_id, from_id, text):
        return

    if await try_route_command(db, peer_id, text_lower):
        return

    if await handle_ai_commands(db, peer_id, text_lower):
        return

    if await try_map_keywords(db, peer_id, text_lower):
        return

    if await try_ai_message(db, peer_id, from_id, text, text_lower):
        return

    if await handle_complaint(db, parsed, peer_id, from_id, text):
        return

    await send_unknown_message(peer_id)

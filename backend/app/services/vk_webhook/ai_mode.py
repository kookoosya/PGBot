"""ИИ-режим VK-бота: состояние peer_id и обработка запросов к Gemini."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.ai_chat import (
    chat_with_ai,
    get_payment_info,
    get_usage_today,
    increment_usage,
    make_identifier,
)
from app.services.vk import get_ai_keyboard, get_welcome_keyboard, send_message
from app.services.vk_ai_history import append_ai_turn, clear_ai_history, get_ai_history
from app.services.vk_messages import (
    ai_enter_text,
    ai_limit_text,
    ai_reply_footer,
    box,
    looks_like_ai_question,
    looks_like_complaint,
)

settings = get_settings()

AI_EXAMPLES = (
    "• Напиши объявление про дрова\n"
    "• Что посмотреть в Пушкиногорье?\n"
    "• Идеи для дачи на лето\n"
    "• Как оформить жалобу в ЖКХ?"
)

# TODO: вынести в БД для multi-worker (аналог vk_flow_states)
_ai_mode_peers: set[int] = set()


def discard_ai_mode(peer_id: int) -> None:
    _ai_mode_peers.discard(peer_id)


def enter_ai_mode(peer_id: int) -> None:
    _ai_mode_peers.add(peer_id)


def is_ai_mode(peer_id: int) -> bool:
    return peer_id in _ai_mode_peers


async def process_vk_ai(db: AsyncSession, peer_id: int, from_id: int, text: str) -> None:
    """Ответ ИИ с учётом лимита и истории диалога."""
    identifier = make_identifier(None, None, vk_id=from_id)
    used = await get_usage_today(db, identifier)
    limit = settings.AI_VK_DAILY_LIMIT

    if used >= limit:
        await send_message(peer_id, ai_limit_text(get_payment_info()), keyboard=get_ai_keyboard())
        return

    history = await get_ai_history(db, peer_id)
    reply = await chat_with_ai(text, history=history)
    await increment_usage(db, identifier, "vk")
    await append_ai_turn(db, peer_id, text, reply)
    remaining = limit - used - 1
    await send_message(
        peer_id,
        f"{reply}{ai_reply_footer(remaining)}",
        keyboard=get_ai_keyboard(),
    )


async def handle_ai_commands(
    db: AsyncSession,
    peer_id: int,
    text_lower: str,
) -> bool:
    """Команды входа/выхода из ИИ и справочные подсказки. True — обработано."""
    site = settings.PUBLIC_SITE_URL.rstrip("/")

    if text_lower in ("🤖 ии-помощник", "ии-помощник", "ии", "ai", "помощник"):
        enter_ai_mode(peer_id)
        await send_message(peer_id, ai_enter_text(), keyboard=get_ai_keyboard())
        return True

    if text_lower in ("💡 примеры вопросов", "примеры"):
        await send_message(peer_id, box("Примеры для ИИ", AI_EXAMPLES), keyboard=get_ai_keyboard())
        return True

    if text_lower in ("🎨 картинки на сайте", "картинки", "нарисуй"):
        await send_message(
            peer_id,
            box(
                "Генерация картинок",
                f"На сайте: {site}/ai → вкладка «Картинки»\n\n"
                "Модели: Flux, Turbo, Nano Banana.\n"
                "Пример: «Уютная изба в снегу» или «Усадьба на закате».\n"
                "Опишите сцену на русском — скачайте результат.",
            ),
            keyboard=get_ai_keyboard(),
        )
        return True

    if text_lower in ("🚪 выйти из ии", "выйти из ии", "стоп"):
        discard_ai_mode(peer_id)
        await clear_ai_history(db, peer_id)
        await send_message(peer_id, "Вернулись в меню 🪶", keyboard=get_welcome_keyboard())
        return True

    return False


async def try_ai_message(
    db: AsyncSession,
    peer_id: int,
    from_id: int,
    text: str,
    text_lower: str,
) -> bool:
    """Обработать сообщение в режиме ИИ или авто-определённый вопрос. True — обработано."""
    if is_ai_mode(peer_id) or text_lower.startswith("ии:"):
        msg = text[3:].strip() if text_lower.startswith("ии:") else text
        if len(msg) < 2:
            await send_message(peer_id, "Напишите вопрос — отвечу в режиме ИИ.", keyboard=get_ai_keyboard())
        else:
            await process_vk_ai(db, peer_id, from_id, msg)
        return True

    if looks_like_ai_question(text) and not looks_like_complaint(text):
        enter_ai_mode(peer_id)
        await process_vk_ai(db, peer_id, from_id, text)
        return True

    return False

import hashlib
import logging
import random
from datetime import date

import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_usage import AIUsage
from app.services.ai_local import local_chat_reply, should_use_local_fallback
from app.services.ai_providers import openrouter_chat, openai_chat, perplexity_chat, pollinations_chat, pollinations_text
from app.services.ai_status import (
    is_valid_gemini_key,
    is_valid_openai_key,
    is_valid_perplexity_key,
    is_valid_openrouter_key,
    is_valid_pollinations_key,
)
from app.utils.errors import ServiceError

logger = logging.getLogger(__name__)
settings = get_settings()

AI_CAPABILITIES: list[str] = []

PUSHKIN_QUOTES = [
    "«Ученье — свет, а неученье — тьма.»",
    "«Труд — вот лучшая зарядка для юности!»",
    "«Береги минуту — час сбережёшь.»",
    "«Всё, что ни делается, — к лучшему.»",
    "«Счастье то, что дух просветляет.»",
]

CHAT_SYSTEM_PROMPT = """Ты — умный и дружелюбный ИИ-помощник портала посёлка Пушкинские Горы (Псковская область).
Здесь жил Александр Сергеевич Пушкин. Ты помогаешь жителям и гостям с любыми задачами:
- вопросы о посёлке, быте, ЖКХ, карте, объявлениях, услугах
- написать текст объявления, пост, поздравление, стихотворение, письмо
- идеи для бизнеса, ремонта, дачи, огорода
- культура, история, маршруты по Пушкиногорью (Михайловское, Тригорское, Святогорская лавра)
- учёба, переводы, расчёты — в разумных пределах
- генерация картинок — на сайте, вкладка «Картинки»

Правила:
- Отвечай на русском, развёрнуто и по делу
- Не выдавай себя за официальное лицо администрации
- Для жалоб — раздел «Жалобы» на сайте или VK-бот
- Будь живым собеседником, не шаблонным ботом
"""


def make_identifier(ip: str | None, user_agent: str | None, vk_id: int | None = None) -> str:
    if vk_id:
        return f"vk:{vk_id}"
    raw = f"{ip or 'unknown'}:{user_agent or 'unknown'}"
    return f"web:{hashlib.sha256(raw.encode()).hexdigest()[:32]}"


class AIValidationError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


class AILimitError(ServiceError):
    def __init__(self, detail: str = "Дневной лимит ИИ исчерпан") -> None:
        super().__init__(detail, status_code=429)


def get_daily_limit(source: str = "web") -> int:
    """Return daily AI message limit for the given source."""
    return settings.AI_VK_DAILY_LIMIT if source == "vk" else settings.AI_FREE_DAILY_LIMIT


def build_limit_reached_reply(limit: int) -> str:
    """Compose a friendly message when the daily AI limit is reached."""
    payment = get_payment_info()
    if payment["card_number"]:
        return (
            f"🪶 Вы использовали {limit} бесплатных сообщений на сегодня.\n\n"
            f"ИИ-помощник работает за счёт добровольных пожертвований.\n\n"
            f"💳 Перевод: {payment['card_number']}\n"
            f"Получатель: {payment['card_holder']}\n"
            f"Сумма: от {payment['amount_suggested']} ₽\n\n"
            f"Завтра лимит обновится!"
        )
    return (
        f"🪶 Вы использовали {limit} бесплатных сообщений на сегодня.\n\n"
        f"{payment['message']}\n\n"
        f"Завтра лимит обновится!"
    )


async def process_public_chat(
    db: AsyncSession,
    *,
    message: str,
    history: list[dict],
    model_id: str | None,
    identifier: str,
) -> dict:
    """Run a public AI chat turn with usage tracking and limit handling."""
    if len(message) > settings.AI_MAX_MESSAGE_LENGTH:
        raise AIValidationError("Сообщение слишком длинное")

    used = await get_usage_today(db, identifier)
    limit = get_daily_limit()
    model = model_id or settings.GEMINI_MODEL

    if used >= limit:
        payment = get_payment_info()
        return {
            "reply": build_limit_reached_reply(limit),
            "remaining": 0,
            "daily_limit": limit,
            "limit_reached": True,
            "payment_info": payment,
            "model": model,
        }

    reply = await chat_with_ai(message, history, model_id=model)
    new_count = await increment_usage(db, identifier, "web")
    return {
        "reply": reply,
        "remaining": max(0, limit - new_count),
        "daily_limit": limit,
        "limit_reached": False,
        "model": model,
    }


async def process_image_generation(
    db: AsyncSession,
    *,
    prompt: str,
    model: str,
    width: int,
    height: int,
    identifier: str,
) -> dict:
    """Generate an image if within daily usage limits."""
    from app.services.ai_media import generate_image

    used = await get_usage_today(db, identifier)
    limit = get_daily_limit()
    if used >= limit:
        raise AILimitError()

    result = await generate_image(prompt, model, width, height)
    if result.get("error"):
        return {
            "url": None,
            "model": model,
            "prompt": prompt,
            "error": result["error"],
        }

    await increment_usage(db, identifier, "web")
    return result


async def get_usage_today(db: AsyncSession, identifier: str) -> int:
    today = date.today()
    result = await db.execute(
        select(AIUsage).where(AIUsage.identifier == identifier, AIUsage.usage_date == today)
    )
    usage = result.scalar_one_or_none()
    return usage.message_count if usage else 0


async def increment_usage(db: AsyncSession, identifier: str, source: str = "web") -> int:
    today = date.today()
    result = await db.execute(
        select(AIUsage).where(AIUsage.identifier == identifier, AIUsage.usage_date == today)
    )
    usage = result.scalar_one_or_none()
    if usage:
        usage.message_count += 1
        count = usage.message_count
    else:
        usage = AIUsage(identifier=identifier, source=source, usage_date=today, message_count=1)
        db.add(usage)
        count = 1
    await db.flush()
    return count


def _maybe_quote(text: str) -> str:
    if random.random() < 0.08:
        return f"{text}\n\n🪶 {random.choice(PUSHKIN_QUOTES)}"
    return text


def _ai_unavailable_message() -> str:
    return "⚠️ ИИ временно недоступен. Попробуйте позже."


async def _chat_gemini(message: str, history: list[dict] | None, model_id: str | None) -> str | None:
    if not is_valid_gemini_key(settings.GEMINI_API_KEY):
        return None
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model_name = model_id if model_id and model_id.startswith("gemini") else settings.GEMINI_MODEL
        model = genai.GenerativeModel(model_name, system_instruction=CHAT_SYSTEM_PROMPT)

        chat_history = []
        if history:
            for msg in history[-6:]:
                role = "user" if msg.get("role") == "user" else "model"
                chat_history.append({"role": role, "parts": [msg.get("content", "")]})

        chat = model.start_chat(history=chat_history)
        response = chat.send_message(message)
        return response.text.strip()
    except Exception as e:
        logger.warning("Gemini chat failed: %s", e)
        return None


async def chat_with_ai(message: str, history: list[dict] | None = None, model_id: str | None = None) -> str:
    model_id = model_id or "openai-fast"

    if model_id.startswith("perplexity") and is_valid_perplexity_key(settings.PERPLEXITY_API_KEY):
        perplexity_text = await perplexity_chat(message, history, CHAT_SYSTEM_PROMPT, model_id)
        if perplexity_text:
            return _maybe_quote(perplexity_text)

    if model_id in ("openai", "openai-fast", "gemini-flash") and is_valid_openai_key(settings.OPENAI_API_KEY):
        openai_text = await openai_chat(message, history, CHAT_SYSTEM_PROMPT, model_id)
        if openai_text:
            return _maybe_quote(openai_text)

    if model_id.startswith("perplexity") and is_valid_openrouter_key(settings.OPENROUTER_API_KEY):
        or_text = await openrouter_chat(message, history, CHAT_SYSTEM_PROMPT, model_id)
        if or_text:
            return _maybe_quote(or_text)

    # 1. Pollinations
    if is_valid_pollinations_key(settings.POLLINATIONS_API_KEY):
        poll_text = await pollinations_chat(message, history, CHAT_SYSTEM_PROMPT, model_id)
        if poll_text:
            return _maybe_quote(poll_text)

    # 2. OpenRouter (GPT / Gemini)
    if is_valid_openrouter_key(settings.OPENROUTER_API_KEY):
        or_text = await openrouter_chat(message, history, CHAT_SYSTEM_PROMPT, model_id)
        if or_text:
            return _maybe_quote(or_text)

    # 3. Прямой OpenAI — резерв для любой модели
    if is_valid_openai_key(settings.OPENAI_API_KEY):
        openai_text = await openai_chat(message, history, CHAT_SYSTEM_PROMPT, model_id)
        if openai_text:
            return _maybe_quote(openai_text)

    # 4. Perplexity — резерв
    if is_valid_perplexity_key(settings.PERPLEXITY_API_KEY):
        perplexity_text = await perplexity_chat(message, history, CHAT_SYSTEM_PROMPT, model_id)
        if perplexity_text:
            return _maybe_quote(perplexity_text)

    # 5. Прямой Gemini
    if model_id not in ("pollinations", "openai-fast", "openai", "perplexity"):
        gemini_text = await _chat_gemini(message, history, model_id)
        if gemini_text:
            return _maybe_quote(gemini_text)

    # 6. Старый GET-текст Pollinations
    if is_valid_pollinations_key(settings.POLLINATIONS_API_KEY):
        lines = [CHAT_SYSTEM_PROMPT, f"Пользователь: {message}", "Ассистент:"]
        poll_text = await pollinations_text("\n".join(lines))
        if poll_text:
            return _maybe_quote(poll_text)

    # 7. Локальный справочник — только для вопросов о посёлке
    if should_use_local_fallback(message):
        return local_chat_reply(message)

    return _ai_unavailable_message()


def get_payment_info() -> dict:
    card = (settings.PAYMENT_CARD_NUMBER or "").strip()
    if card:
        payment_hint = (
            f"ИИ-помощник работает за счёт добровольных переводов — от {settings.PAYMENT_AMOUNT_SUGGESTED} ₽. "
            "Объявления, услуги и жалобы на портале бесплатны."
        )
    else:
        payment_hint = (
            "ИИ-помощник работает за счёт добровольных пожертвований. "
            f"Реквизиты уточняйте по {settings.PAYMENT_CONTACT_EMAIL}. "
            "Объявления, услуги и жалобы на портале бесплатны."
        )
    return {
        "card_number": card,
        "card_holder": settings.PAYMENT_CARD_HOLDER,
        "bank_name": settings.PAYMENT_BANK_NAME,
        "description": settings.PAYMENT_DESCRIPTION,
        "amount_suggested": settings.PAYMENT_AMOUNT_SUGGESTED,
        "contact_email": settings.PAYMENT_CONTACT_EMAIL,
        "message": payment_hint,
    }

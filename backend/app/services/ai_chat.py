import hashlib
import logging
import random
from datetime import date

import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_usage import AIUsage
from app.models.user import User
from app.services.ai_entitlement_service import resolve_ai_access
from app.services.ai_local import local_chat_reply, should_use_local_fallback
from app.services.ai_plans import CHAT_MODE_PROMPTS, plan_by_id
from app.services.ai_providers import openrouter_chat, openai_chat, pollinations_chat, pollinations_text
from app.services.ai_status import (
    is_valid_gemini_key,
    is_valid_openai_key,
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


def make_identifier(
    ip: str | None,
    user_agent: str | None,
    vk_id: int | None = None,
    user_id: int | None = None,
) -> str:
    if user_id:
        return f"user:{user_id}"
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


def build_limit_reached_reply(limit: int, *, is_paid: bool = False, plan_name: str = "Бесплатно") -> str:
    """Compose a friendly message when the daily AI limit is reached."""
    payment = get_payment_info()
    if is_paid:
        return (
            f"🪶 Лимит тарифа «{plan_name}» на сегодня исчерпан ({limit} сообщений).\n\n"
            "Завтра счётчик обновится. Если нужен больший объём — напишите администратору."
        )
    pro = plan_by_id("pro")
    pro_price = pro.price_rub if pro else settings.AI_PRO_PRICE
    if payment["card_number"]:
        return (
            f"🪶 Бесплатный лимит исчерпан — {limit} сообщений на сегодня.\n\n"
            f"Постоянный доступ — тариф «ИИ Pro» {pro_price} ₽/мес переводом на карту.\n\n"
            f"💳 {payment['card_number']}\n"
            f"👤 {payment['card_holder']}\n"
            f"💰 {pro_price} ₽ · ИИ Pro\n\n"
            f"Завтра бесплатные {limit} сообщений снова доступны."
        )
    return (
        f"🪶 Бесплатный лимит исчерпан — {limit} сообщений на сегодня.\n\n"
        f"{payment['message']}\n\n"
        f"Завтра бесплатные {limit} сообщений снова доступны."
    )


def build_system_prompt(chat_mode: str = "chat") -> str:
    prompt = CHAT_SYSTEM_PROMPT
    extra = CHAT_MODE_PROMPTS.get(chat_mode)
    if extra:
        prompt += extra
    return prompt


async def process_public_chat(
    db: AsyncSession,
    *,
    message: str,
    history: list[dict],
    model_id: str | None,
    identifier: str,
    user: User | None = None,
    chat_mode: str = "chat",
) -> dict:
    """Run a public AI chat turn with usage tracking and limit handling."""
    if len(message) > settings.AI_MAX_MESSAGE_LENGTH:
        raise AIValidationError("Сообщение слишком длинное")

    access = await resolve_ai_access(db, user=user, web_identifier=identifier)
    if chat_mode not in access["chat_modes"]:
        raise AIValidationError("Этот режим доступен в пробном периоде и тарифе ИИ Pro")

    used = await get_usage_today(db, identifier)
    limit = access["daily_limit"]
    model = model_id or access["model_id"]

    if used >= limit:
        payment = get_payment_info()
        return {
            "reply": build_limit_reached_reply(
                limit,
                is_paid=access["is_paid"],
                plan_name=access["plan_name"],
            ),
            "remaining": 0,
            "daily_limit": limit,
            "limit_reached": True,
            "payment_info": payment,
            "model": model,
            "plan_id": access["plan_id"],
            "plan_name": access["plan_name"],
            "is_paid": access["is_paid"],
        }

    system_prompt = build_system_prompt(chat_mode)
    gemini_used = await get_gemini_usage_today(db, identifier)
    allow_gemini = gemini_used < settings.AI_GEMINI_DAILY_LIMIT
    reply, provider = await chat_with_ai(
        message,
        history,
        model_id=model,
        system_prompt=system_prompt,
        prefer_paid_providers=access["is_paid"],
        allow_gemini=allow_gemini,
    )
    new_count = await increment_usage(
        db,
        identifier,
        "web",
        via_gemini=provider == "gemini",
    )
    return {
        "reply": reply,
        "remaining": max(0, limit - new_count),
        "daily_limit": limit,
        "limit_reached": False,
        "model": model,
        "plan_id": access["plan_id"],
        "plan_name": access["plan_name"],
        "is_paid": access["is_paid"],
    }


async def process_image_generation(
    db: AsyncSession,
    *,
    prompt: str,
    model: str,
    width: int,
    height: int,
    identifier: str,
    user: User | None = None,
) -> dict:
    """Generate an image if within daily usage limits."""
    from app.services.ai_media import generate_image

    access = await resolve_ai_access(db, user=user, web_identifier=identifier)
    used = await get_usage_today(db, identifier)
    limit = access["daily_limit"]
    if used >= limit:
        raise AILimitError(
            build_limit_reached_reply(limit, is_paid=access["is_paid"], plan_name=access["plan_name"]),
        )

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


async def get_gemini_usage_today(db: AsyncSession, identifier: str) -> int:
    today = date.today()
    result = await db.execute(
        select(AIUsage).where(AIUsage.identifier == identifier, AIUsage.usage_date == today)
    )
    usage = result.scalar_one_or_none()
    return usage.gemini_count if usage else 0


async def increment_usage(
    db: AsyncSession,
    identifier: str,
    source: str = "web",
    *,
    via_gemini: bool = False,
) -> int:
    today = date.today()
    result = await db.execute(
        select(AIUsage).where(AIUsage.identifier == identifier, AIUsage.usage_date == today)
    )
    usage = result.scalar_one_or_none()
    if usage:
        usage.message_count += 1
        if via_gemini:
            usage.gemini_count += 1
        count = usage.message_count
    else:
        usage = AIUsage(
            identifier=identifier,
            source=source,
            usage_date=today,
            message_count=1,
            gemini_count=1 if via_gemini else 0,
        )
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


async def _chat_gemini(
    message: str,
    history: list[dict] | None,
    model_id: str | None,
    system_prompt: str,
) -> str | None:
    if not is_valid_gemini_key(settings.GEMINI_API_KEY):
        return None
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
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
    except Exception as e:
        logger.warning("Gemini chat failed: %s", e)
        return None


async def chat_with_ai(
    message: str,
    history: list[dict] | None = None,
    model_id: str | None = None,
    system_prompt: str | None = None,
    *,
    prefer_paid_providers: bool = False,
    allow_gemini: bool = True,
) -> tuple[str, str | None]:
    model_id = model_id or "gemini-flash"
    prompt = system_prompt or CHAT_SYSTEM_PROMPT

    if prefer_paid_providers and is_valid_pollinations_key(settings.POLLINATIONS_API_KEY):
        poll_text = await pollinations_chat(message, history, prompt, model_id)
        if poll_text:
            return _maybe_quote(poll_text), "pollinations"

    if model_id in ("openai", "openai-fast") and is_valid_openai_key(settings.OPENAI_API_KEY):
        openai_text = await openai_chat(message, history, prompt, model_id)
        if openai_text:
            return _maybe_quote(openai_text), "openai"

    if is_valid_pollinations_key(settings.POLLINATIONS_API_KEY):
        poll_text = await pollinations_chat(message, history, prompt, model_id)
        if poll_text:
            return _maybe_quote(poll_text), "pollinations"

    if is_valid_openrouter_key(settings.OPENROUTER_API_KEY):
        or_text = await openrouter_chat(message, history, prompt, model_id)
        if or_text:
            return _maybe_quote(or_text), "openrouter"

    if is_valid_openai_key(settings.OPENAI_API_KEY):
        openai_text = await openai_chat(message, history, prompt, model_id)
        if openai_text:
            return _maybe_quote(openai_text), "openai"

    if allow_gemini and model_id not in ("pollinations", "openai-fast", "openai"):
        gemini_text = await _chat_gemini(message, history, model_id, prompt)
        if gemini_text:
            return _maybe_quote(gemini_text), "gemini"

    if is_valid_pollinations_key(settings.POLLINATIONS_API_KEY):
        lines = [prompt, f"Пользователь: {message}", "Ассистент:"]
        poll_text = await pollinations_text("\n".join(lines))
        if poll_text:
            return _maybe_quote(poll_text), "pollinations"

    if should_use_local_fallback(message):
        return local_chat_reply(message), "local"

    return _ai_unavailable_message(), None


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

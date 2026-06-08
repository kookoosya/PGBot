import hashlib
import logging
import random
from datetime import date

import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_usage import AIUsage
from app.services.ai_providers import pollinations_text

logger = logging.getLogger(__name__)
settings = get_settings()

PUSHKIN_QUOTES = [
    "«Ученье — свет, а неученье — тьма.»",
    "«Труд — вот лучшая зарядка для юности!»",
    "«Береги минуту — час сбережёшь.»",
    "«Всё, что ни делается, — к лучшему.»",
    "«Счастье то, что дух просветляет.»",
]

CHAT_SYSTEM_PROMPT = """Ты — мощный универсальный ИИ-помощник портала посёлка Пушкинские Горы (Псковская область).
Здесь жил Александр Сергеевич Пушкин. Ты можешь помочь с ЛЮБЫМИ задачами:
- вопросы о посёлке, быте, ЖКХ, карте, объявлениях, услугах
- написать текст объявления, пост, поздравление, письмо
- идеи для бизнеса, ремонта, дачи, огорода
- культура, история, маршруты по Пушкиногорью
- программирование, учёба, переводы, расчёты — всё в разумных пределах
- подсказать, как сгенерировать картинку на сайте (раздел «Картинки»)

На сайте доступны модели: Gemini Flash/Pro для текста, Nano Banana / Flux / Turbo для картинок.

Правила:
- Отвечай на русском, полезно и по делу (до 400 слов)
- Не выдавай себя за официальное лицо администрации
- Для жалоб на проблемы — бот ВК или сайт
- Будь дружелюбным собеседником
"""


def make_identifier(ip: str | None, user_agent: str | None, vk_id: int | None = None) -> str:
    if vk_id:
        return f"vk:{vk_id}"
    raw = f"{ip or 'unknown'}:{user_agent or 'unknown'}"
    return f"web:{hashlib.sha256(raw.encode()).hexdigest()[:32]}"


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


def _build_pollinations_prompt(message: str, history: list[dict] | None) -> str:
    lines = [CHAT_SYSTEM_PROMPT, ""]
    if history:
        for msg in history[-6:]:
            role = "Пользователь" if msg.get("role") == "user" else "Ассистент"
            lines.append(f"{role}: {msg.get('content', '')}")
    lines.append(f"Пользователь: {message}")
    lines.append("Ассистент:")
    return "\n".join(lines)


async def _chat_gemini(message: str, history: list[dict] | None, model_id: str | None) -> str | None:
    if not settings.GEMINI_API_KEY:
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
        logger.warning("Gemini chat failed, using fallback: %s", e)
        return None


async def chat_with_ai(message: str, history: list[dict] | None = None, model_id: str | None = None) -> str:
    use_pollinations_only = model_id == "pollinations"

    if not use_pollinations_only:
        gemini_text = await _chat_gemini(message, history, model_id)
        if gemini_text:
            if random.random() < 0.12:
                gemini_text += f"\n\n🪶 {random.choice(PUSHKIN_QUOTES)}"
            return gemini_text

    poll_prompt = _build_pollinations_prompt(message, history)
    poll_text = await pollinations_text(poll_prompt)
    if poll_text:
        if random.random() < 0.1:
            poll_text += f"\n\n🪶 {random.choice(PUSHKIN_QUOTES)}"
        return poll_text

    quote = random.choice(PUSHKIN_QUOTES)
    return (
        f"🪶 {quote}\n\n"
        "Сейчас не удалось получить ответ от ИИ. Попробуйте ещё раз через минуту "
        "или выберите модель «Pollinations (резерв)»."
    )


def get_payment_info() -> dict:
    return {
        "card_number": settings.PAYMENT_CARD_NUMBER,
        "card_holder": settings.PAYMENT_CARD_HOLDER,
        "bank_name": settings.PAYMENT_BANK_NAME,
        "description": settings.PAYMENT_DESCRIPTION,
        "amount_suggested": settings.PAYMENT_AMOUNT_SUGGESTED,
        "contact_email": settings.PAYMENT_CONTACT_EMAIL,
        "message": (
            f"ИИ-помощник работает за счёт добровольных переводов — от {settings.PAYMENT_AMOUNT_SUGGESTED} ₽. "
            "Объявления, услуги и жалобы на портале бесплатны."
        ),
    }

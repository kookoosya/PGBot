import hashlib
import logging
import random
from datetime import date

import google.generativeai as genai
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_usage import AIUsage

logger = logging.getLogger(__name__)
settings = get_settings()

PUSHKIN_QUOTES = [
    "«Ученье — свет, а неученье — тьма.»",
    "«Труд — вот лучшая зарядка для юности!»",
    "«Береги минуту — час сбережёшь.»",
    "«Всё, что ни делается, — к лучшему.»",
    "«Счастье то, что дух просветляет.»",
]

CHAT_SYSTEM_PROMPT = """Ты — умный и дружелюбный ИИ-помощник поселка Пушкинские Горы (Псковская область).
Здесь жил и творил Александр Сергеевич Пушкин. Твой стиль — тёплый, культурный, с лёгкими
отсылками к поэзии, но без пафоса. Ты помогаешь жителям с вопросами о:
- жизни в поселке, быте, ЖКХ
- культуре, истории Пушкинских Гор
- подготовке обращений в народный контроль
- общих вопросах (в разумных пределах)

Правила:
- Отвечай на русском, кратко и по делу (до 300 слов)
- Не выдавай себя за официальное лицо администрации
- Для жалоб на проблемы посоветуй написать боту или на сайт
- Будь полезным и интересным собеседником
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


async def chat_with_ai(message: str, history: list[dict] | None = None) -> str:
    if not settings.GEMINI_API_KEY:
        quote = random.choice(PUSHKIN_QUOTES)
        return (
            f"🪶 {quote}\n\n"
            "ИИ-помощник временно работает в демо-режиме. "
            "Для полноценных ответов администратору нужно настроить GEMINI_API_KEY.\n\n"
            f"Ваш вопрос: «{message[:100]}» — принят! "
            "А пока напишите боту ВКонтакте, если нужно отправить обращение."
        )

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(
            settings.GEMINI_MODEL,
            system_instruction=CHAT_SYSTEM_PROMPT,
        )

        chat_history = []
        if history:
            for msg in history[-6:]:
                role = "user" if msg.get("role") == "user" else "model"
                chat_history.append({"role": role, "parts": [msg.get("content", "")]})

        chat = model.start_chat(history=chat_history)
        response = chat.send_message(message)
        text = response.text.strip()

        if random.random() < 0.15:
            text += f"\n\n🪶 {random.choice(PUSHKIN_QUOTES)}"

        return text
    except Exception as e:
        logger.error("AI chat failed: %s", e)
        return (
            "Простите, сейчас не могу ответить — сервер ИИ перегружен. "
            "Попробуйте через несколько минут или напишите в бот ВКонтакте."
        )


def get_payment_info() -> dict:
    return {
        "card_number": settings.PAYMENT_CARD_NUMBER,
        "amount_suggested": settings.PAYMENT_AMOUNT_SUGGESTED,
        "message": (
            f"Поддержите портал посёлка — от {settings.PAYMENT_AMOUNT_SUGGESTED} ₽. "
            "Перевод на карту помогает развивать сайт."
        ),
    }

"""Тексты и форматирование сообщений VK-бота."""

from app.config import get_settings
from app.services.site_urls import public_site_url

settings = get_settings()

SEP = "━━━━━━━━━━━━━━━"


def box(title: str, body: str) -> str:
    return f"🪶 {title}\n{SEP}\n{body}"


def welcome_text() -> str:
    return box(
        "Пушкинские Горы",
        "Портал посёлка в VK — как на сайте.\n\n"
        "🗺 Карта · 💼 Работа · 📋 Объявления\n"
        "🌤 Погода · ➕ Подать объявление без регистрации\n"
        "🛤 Маршруты · ⚠️ Жалобы · 🤖 ИИ\n\n"
        "✨ Объявления и жалобы — бесплатно\n"
        f"💬 ИИ — {settings.AI_VK_DAILY_LIMIT} сообщений/день\n\n"
        f"🌐 {public_site_url()}",
    )


def ai_enter_text() -> str:
    return box(
        "ИИ-помощник",
        "Спросите что угодно — отвечу сразу в чате.\n\n"
        f"🆓 Бесплатно: {settings.AI_VK_DAILY_LIMIT} сообщений в день\n"
        "🎨 Картинки — на сайте (Flux, Turbo, Nano Banana)\n"
        "   Опишите сцену на русском — портал нарисует.\n\n"
        "Кнопка «Выйти из ИИ» — обратно в меню.",
    )


def ai_limit_text(payment: dict) -> str:
    return box(
        "Лимит ИИ на сегодня",
        f"Бесплатные {settings.AI_VK_DAILY_LIMIT} сообщений использованы.\n\n"
        "ИИ работает за счёт добровольных переводов:\n"
        f"💳 {payment['card_number']}\n"
        f"👤 {payment['card_holder']}\n"
        f"💰 от {payment['amount_suggested']} ₽\n\n"
        "Завтра лимит обновится.\n"
        f"🎨 Картинки: {public_site_url()}/ai",
    )


def ai_reply_footer(remaining: int) -> str:
    return f"\n{SEP}\n💬 ИИ сегодня: {max(0, remaining)} · 🎨 {public_site_url()}/ai"


def help_text() -> str:
    return box(
        "Справка",
        "🗺 Карта — «аптека», «магазин», «музей»\n"
        "🗺 Ошибка карты — неверный телефон или адрес\n"
        "💼 Работа — вакансии соседей\n"
        "➕ Объявление — подать без регистрации (4 шага)\n"
        "📋 Объявления — свежие на доске\n"
        "🛤 Маршруты — куда сходить туристу\n"
        "🌤 Погода — сейчас и по часам\n"
        "🛠 Услуги — мастера, огород, дрова\n"
        "⚠️ Жалобы — опишите проблему или фото\n"
        "💡 Пожелания — идеи для портала (в чате)\n"
        "🚕 Такси — телефоны\n"
        "🤖 ИИ — вопросы, тексты\n"
        "🔔 Подписаться / отписаться\n"
        "   «подписка работа», «подписка дрова», «подписка сосед»\n\n"
        f"🌐 {public_site_url()}",
    )


def looks_like_ai_question(text: str) -> bool:
    t = text.lower().strip()
    if len(t) < 6:
        return False
    if t.endswith("?"):
        return True
    prefixes = (
        "как ", "что ", "где ", "когда ", "почему ", "сколько ",
        "подскажи", "напиши", "объясни", "придумай", "переведи",
        "помоги", "расскажи", "составь", "ии ",
    )
    return any(t.startswith(p) for p in prefixes)


def looks_like_complaint(text: str) -> bool:
    t = text.lower()
    if len(t) < 12:
        return False
    markers = (
        "жалоб", "обращен", "не работает", "сломан", "проблем",
        "авария", "мусор", "фонар", "дорог", "жкх", "утечк",
        "нет воды", "яма", "просит", "разбит", "опасн",
    )
    return any(m in t for m in markers)

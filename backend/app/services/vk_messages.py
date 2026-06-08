"""Тексты и форматирование сообщений VK-бота."""

from app.config import get_settings

settings = get_settings()
_SITE = settings.PUBLIC_SITE_URL.rstrip("/")

SEP = "━━━━━━━━━━━━━━━"


def box(title: str, body: str) -> str:
    return f"🪶 {title}\n{SEP}\n{body}"


def welcome_text() -> str:
    return box(
        "Пушкинские Горы",
        "Портал посёлка в VK — как на сайте.\n\n"
        "🗺 Карта · 📋 Объявления · 🛠 Услуги\n"
        "⚠️ Жалобы · 🤖 ИИ-помощник\n\n"
        "✨ Объявления, услуги и жалобы — бесплатно\n"
        f"💬 ИИ — {settings.AI_VK_DAILY_LIMIT} сообщений/день бесплатно\n\n"
        f"🌐 {_SITE}",
    )


def ai_enter_text() -> str:
    return box(
        "ИИ-помощник",
        "Спросите что угодно — отвечу сразу в чате.\n\n"
        f"🆓 Бесплатно: {settings.AI_VK_DAILY_LIMIT} сообщений в день\n"
        "🎨 Картинки — на сайте (Nano Banana, Flux…)\n\n"
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
        f"🎨 Картинки: {_SITE}/ai",
    )


def ai_reply_footer(remaining: int) -> str:
    return f"\n{SEP}\n💬 ИИ сегодня: {max(0, remaining)} · 🎨 {_SITE}/ai"


def help_text() -> str:
    return box(
        "Справка",
        "🗺 Карта — магазины, аптеки, кафе\n"
        "📋 Объявления — бесплатно\n"
        "🛠 Услуги — мастера, огород, дрова\n"
        "⚠️ Жалобы — опишите проблему\n"
        "🤖 ИИ — вопросы, тексты, идеи\n"
        "📝 Регистрация — жители, ЖКХ, организации\n"
        "🔔 Подписаться — новые объявления\n\n"
        f"🌐 {_SITE}",
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

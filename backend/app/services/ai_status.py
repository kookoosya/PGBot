"""Статус AI-провайдеров на сервере."""

from app.config import get_settings

_PLACEHOLDER_MARKERS = ("your-gemini", "your-gemini-api-key", "change-me", "example")


def _looks_like_placeholder(key: str) -> bool:
    low = key.strip().lower()
    if not low:
        return True
    return any(m in low for m in _PLACEHOLDER_MARKERS) or len(low) < 24


def is_valid_gemini_key(key: str) -> bool:
    k = key.strip()
    return bool(k) and not _looks_like_placeholder(k) and (
        k.startswith("AIza") or k.startswith("AQ.") or len(k) >= 32
    )


def is_valid_pollinations_key(key: str) -> bool:
    """Ключ для чата Pollinations (sk_/pk_ или Google AQ.)."""
    k = key.strip()
    if not k or _looks_like_placeholder(k):
        return False
    return k.startswith(("sk_", "pk_", "AQ."))


def is_valid_pollinations_image_key(key: str) -> bool:
    """Ключ для картинок Pollinations — только sk_/pk_ с enter.pollinations.ai."""
    k = key.strip()
    if not k or _looks_like_placeholder(k):
        return False
    return k.startswith(("sk_", "pk_"))


def is_valid_openrouter_key(key: str) -> bool:
    k = key.strip()
    return bool(k) and k.startswith("sk-or-")


def is_valid_openai_key(key: str) -> bool:
    k = key.strip()
    if not k or _looks_like_placeholder(k):
        return False
    return k.startswith("sk-") and not k.startswith("sk-or-")


def is_valid_perplexity_key(key: str) -> bool:
    k = key.strip()
    if not k or _looks_like_placeholder(k):
        return False
    return k.startswith("pplx-")


def get_ai_status() -> dict:
    s = get_settings()
    poll_ok = is_valid_pollinations_key(s.POLLINATIONS_API_KEY)
    poll_img_ok = is_valid_pollinations_image_key(s.POLLINATIONS_API_KEY)
    or_ok = is_valid_openrouter_key(s.OPENROUTER_API_KEY)
    openai_ok = is_valid_openai_key(s.OPENAI_API_KEY)
    perplexity_ok = is_valid_perplexity_key(s.PERPLEXITY_API_KEY)
    gemini_ok = is_valid_gemini_key(s.GEMINI_API_KEY)

    if openai_ok:
        chat_provider = "openai"
    elif poll_ok:
        chat_provider = "pollinations"
    elif or_ok:
        chat_provider = "openrouter"
    elif perplexity_ok:
        chat_provider = "perplexity"
    elif gemini_ok:
        chat_provider = "google"
    else:
        chat_provider = "local"

    if poll_img_ok:
        image_provider = "pollinations"
    elif or_ok:
        image_provider = "openrouter"
    else:
        image_provider = "local-poster"

    ready = chat_provider != "local"

    if openai_ok:
        message = "ИИ работает (ChatGPT)."
    elif poll_ok:
        if poll_img_ok or or_ok:
            message = "ИИ работает."
        else:
            message = "Чат работает. Картинки временно недоступны."
    elif or_ok:
        message = "ИИ работает."
    elif perplexity_ok:
        message = "ИИ работает (Perplexity)."
    elif gemini_ok:
        message = "ИИ работает (только чат)."
    else:
        ready = False
        if s.GEMINI_API_KEY.strip() and not gemini_ok:
            message = "Ключ Gemini на сервере — заглушка. Нужен OPENAI_API_KEY, OPENROUTER_API_KEY или POLLINATIONS_API_KEY."
        else:
            message = "ИИ не настроен: нет рабочего API-ключа на сервере."

    providers = []
    if openai_ok:
        providers.append("ChatGPT (OpenAI)")
    if perplexity_ok:
        providers.append("Perplexity")
    if poll_ok:
        providers.append("Pollinations")
    if or_ok:
        providers.append("OpenRouter")
    if gemini_ok:
        providers.append("Gemini")

    provider_notes = []
    if openai_ok:
        provider_notes.append("ChatGPT — ваш ключ OpenAI, у него свои лимиты на account.openai.com")
    if perplexity_ok:
        provider_notes.append("Perplexity — бесплатный тариф с ограничениями на perplexity.ai/settings/api")
    if poll_ok or or_ok or gemini_ok:
        provider_notes.append("резервные провайдеры тоже с лимитами")

    return {
        "ready": ready,
        "chat_provider": chat_provider,
        "image_provider": image_provider,
        "pollinations_configured": poll_ok,
        "openrouter_configured": or_ok,
        "openai_configured": openai_ok,
        "perplexity_configured": perplexity_ok,
        "gemini_configured": gemini_ok,
        "providers": providers,
        "message": message,
        "limits": {
            "site_daily": s.AI_FREE_DAILY_LIMIT,
            "site_note": (
                f"На портале — {s.AI_FREE_DAILY_LIMIT} бесплатных сообщений в день на человека. "
                "Лимит обновляется в полночь."
            ),
            "providers_note": (
                "У каждого AI-провайдера свои лимиты и кредиты. "
                + ("; ".join(provider_notes) + "." if provider_notes else "При исчерпании ответ может быть недоступен.")
            ),
        },
    }

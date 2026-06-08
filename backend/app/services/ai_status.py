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


def get_ai_status() -> dict:
    s = get_settings()
    poll_ok = is_valid_pollinations_key(s.POLLINATIONS_API_KEY)
    poll_img_ok = is_valid_pollinations_image_key(s.POLLINATIONS_API_KEY)
    or_ok = is_valid_openrouter_key(s.OPENROUTER_API_KEY)
    gemini_ok = is_valid_gemini_key(s.GEMINI_API_KEY)

    if poll_ok:
        chat_provider = "pollinations"
        if poll_img_ok:
            image_provider = "pollinations"
            ready = True
            message = "ИИ работает."
        elif or_ok:
            image_provider = "openrouter"
            ready = True
            message = "ИИ работает."
        else:
            image_provider = "local-poster"
            ready = True
            message = "Чат работает. Картинки временно недоступны."
    elif or_ok:
        chat_provider = "openrouter"
        image_provider = "openrouter"
        ready = True
        message = "ИИ работает."
    elif gemini_ok:
        chat_provider = "google"
        image_provider = "local-fallback"
        ready = True
        message = "ИИ работает (только чат)."
    else:
        chat_provider = "local"
        image_provider = "local-poster"
        ready = False
        if s.GEMINI_API_KEY.strip() and not gemini_ok:
            message = "Ключ Gemini на сервере — заглушка. Нужен OPENROUTER_API_KEY или POLLINATIONS_API_KEY."
        else:
            message = "ИИ не настроен: нет рабочего API-ключа на сервере."

    providers = []
    if poll_ok:
        providers.append("Pollinations")
    if or_ok:
        providers.append("OpenRouter")
    if gemini_ok:
        providers.append("Gemini")

    return {
        "ready": ready,
        "chat_provider": chat_provider,
        "image_provider": image_provider,
        "pollinations_configured": poll_ok,
        "openrouter_configured": or_ok,
        "gemini_configured": gemini_ok,
        "providers": providers,
        "message": message,
        "limits": {
            "site_daily": s.AI_FREE_DAILY_LIMIT,
            "site_note": f"{s.AI_FREE_DAILY_LIMIT} запросов в день на человека.",
            "providers_note": "",
        },
    }

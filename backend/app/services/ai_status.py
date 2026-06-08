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
    return bool(k) and not _looks_like_placeholder(k) and (k.startswith("AIza") or len(k) >= 32)


def is_valid_pollinations_key(key: str) -> bool:
    k = key.strip()
    return bool(k) and (k.startswith("sk_") or k.startswith("pk_"))


def get_ai_status() -> dict:
    s = get_settings()
    poll_ok = is_valid_pollinations_key(s.POLLINATIONS_API_KEY)
    gemini_ok = is_valid_gemini_key(s.GEMINI_API_KEY)

    if poll_ok:
        chat_provider = "pollinations"
        image_provider = "pollinations"
        ready = True
        message = "ИИ подключён через Pollinations (чат и картинки)."
    elif gemini_ok:
        chat_provider = "google"
        image_provider = "local-fallback"
        ready = True
        message = "Чат через Gemini. Для картинок добавьте POLLINATIONS_API_KEY."
    else:
        chat_provider = "local"
        image_provider = "local-poster"
        ready = False
        if s.GEMINI_API_KEY.strip() and not gemini_ok:
            message = "Ключ Gemini на сервере недействителен (заглушка из .env.example). Нужен POLLINATIONS_API_KEY или рабочий GEMINI_API_KEY."
        else:
            message = "ИИ не настроен: добавьте POLLINATIONS_API_KEY на сервер."

    return {
        "ready": ready,
        "chat_provider": chat_provider,
        "image_provider": image_provider,
        "pollinations_configured": poll_ok,
        "gemini_configured": gemini_ok,
        "message": message,
    }

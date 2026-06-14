"""Генерация изображений и список AI-моделей."""

import logging

from app.config import get_settings
from app.services.ai_image_fallback import save_fallback_image
from app.services.ai_image_store import save_image
from app.services.ai_prompt_translate import image_prompt_english
from app.services.ai_providers import openrouter_image_bytes, pollinations_image_bytes
from app.services.ai_status import (
    is_valid_gemini_key,
    is_valid_openai_key,
    is_valid_openrouter_key,
    is_valid_pollinations_key,
    is_valid_pollinations_image_key,
)

logger = logging.getLogger(__name__)
settings = get_settings()

CHAT_MODELS_FALLBACK = [
    {"id": "gemini-flash", "label": "Быстрый", "provider": "pollinations", "fast": True},
    {"id": "openai", "label": "Умный", "provider": "pollinations", "smart": True},
]


def get_chat_models() -> list[dict]:
    models: list[dict] = []
    if is_valid_openai_key(settings.OPENAI_API_KEY):
        models.append(
            {"id": "openai-fast", "label": "ChatGPT — быстрый", "provider": "openai", "fast": True},
        )
        models.append(
            {"id": "openai", "label": "ChatGPT — умный (Pro)", "provider": "openai", "smart": True},
        )
    if models:
        return models
    if is_valid_pollinations_key(settings.POLLINATIONS_API_KEY) or is_valid_openrouter_key(
        settings.OPENROUTER_API_KEY,
    ):
        return CHAT_MODELS_FALLBACK
    if is_valid_gemini_key(settings.GEMINI_API_KEY):
        return [{"id": "gemini-flash", "label": "Gemini", "provider": "google", "fast": True}]
    return CHAT_MODELS_FALLBACK

IMAGE_MODELS = [
    {"id": "flux", "label": "Flux", "provider": "pollinations"},
    {"id": "turbo", "label": "Turbo", "provider": "pollinations"},
]

POLLINATIONS_MODEL_MAP = {
    "nano-banana": "nanobanana",
    "nanobanana": "nanobanana",
    "flux": "flux",
    "turbo": "turbo",
}


async def generate_image(prompt: str, model: str = "flux", width: int = 1024, height: int = 1024) -> dict:
    prompt = prompt.strip()[:500]
    if not prompt:
        return {"error": "Пустой запрос"}

    en_prompt = image_prompt_english(prompt)

    # Pollinations Flux — бесплатно по pollen
    if is_valid_pollinations_image_key(settings.POLLINATIONS_API_KEY):
        poll_model = POLLINATIONS_MODEL_MAP.get(model, "flux")
        data = await pollinations_image_bytes(en_prompt, model=poll_model, width=width, height=height)
        if not data:
            data = await pollinations_image_bytes(prompt[:200], model=poll_model, width=width, height=height)
        if data:
            image_id = save_image(data, "jpg")
            return {
                "url": f"/api/v1/ai/images/{image_id}",
                "model": model,
                "prompt": prompt,
                "provider": "pollinations",
            }

    # OpenRouter — резерв, если есть кредиты
    if is_valid_openrouter_key(settings.OPENROUTER_API_KEY):
        data = await openrouter_image_bytes(en_prompt, model=model)
        if not data:
            data = await openrouter_image_bytes(prompt, model=model)
        if data:
            ext = "png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "jpg"
            image_id = save_image(data, ext)
            return {
                "url": f"/api/v1/ai/images/{image_id}",
                "model": model,
                "prompt": prompt,
                "provider": "openrouter",
            }

    if settings.GEMINI_API_KEY and model == "gemini-imagen":
        result = await _generate_gemini_image(prompt)
        if result:
            return result

    if not is_valid_openrouter_key(settings.OPENROUTER_API_KEY) and not is_valid_pollinations_image_key(
        settings.POLLINATIONS_API_KEY
    ):
        return {"error": "Генератор картинок не настроен: нет API-ключа на сервере."}

    fallback_id = save_fallback_image(prompt)
    if fallback_id:
        return {
            "url": f"/api/v1/ai/images/{fallback_id}",
            "model": model,
            "prompt": prompt,
            "provider": "local-poster",
        }
    return {"error": "Не удалось сгенерировать изображение. Попробуйте упростить описание."}


async def _generate_gemini_image(prompt: str) -> dict | None:
    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(
            f"Generate an image: {prompt}",
            generation_config={"response_modalities": ["TEXT", "IMAGE"]},
        )
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                mime = part.inline_data.mime_type or "image/png"
                ext = "png" if "png" in mime else "jpg"
                image_id = save_image(part.inline_data.data, ext)
                return {
                    "url": f"/api/v1/ai/images/{image_id}",
                    "model": "gemini-imagen",
                    "prompt": prompt,
                    "provider": "google",
                }
    except Exception as exc:
        logger.warning("Gemini image gen unavailable: %s", exc)
    return None

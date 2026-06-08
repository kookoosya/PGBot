"""Генерация изображений и список AI-моделей."""

import logging

from app.config import get_settings
from app.services.ai_image_fallback import save_fallback_image
from app.services.ai_image_store import save_image
from app.services.ai_prompt_translate import image_prompt_english
from app.services.ai_providers import pollinations_image_bytes
from app.services.ai_status import is_valid_pollinations_key

logger = logging.getLogger(__name__)
settings = get_settings()

CHAT_MODELS = [
    {"id": "gemini-flash", "label": "Gemini Flash", "provider": "pollinations", "fast": True},
    {"id": "openai-fast", "label": "GPT Fast", "provider": "pollinations", "fast": True},
    {"id": "gemini", "label": "Gemini Pro", "provider": "pollinations", "smart": True},
    {"id": "gemini-2.0-flash", "label": "Gemini (прямой Google)", "provider": "google", "fast": True},
]

IMAGE_MODELS = [
    {"id": "flux", "label": "Flux", "provider": "pollinations", "desc": "Реалистичные иллюстрации"},
    {"id": "turbo", "label": "Turbo", "provider": "pollinations", "desc": "Быстрая генерация"},
    {"id": "nanobanana", "label": "Nano Banana", "provider": "pollinations", "desc": "Яркий стиль"},
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

    if settings.GEMINI_API_KEY and model == "gemini-imagen":
        result = await _generate_gemini_image(prompt)
        if result:
            return result

    poll_model = POLLINATIONS_MODEL_MAP.get(model, "flux")
    en_prompt = image_prompt_english(prompt)
    data = await pollinations_image_bytes(en_prompt, model=poll_model, width=width, height=height)
    if not data and en_prompt != prompt:
        data = await pollinations_image_bytes(prompt[:200], model=poll_model, width=width, height=height)
    if not data:
        data = await pollinations_image_bytes(
            "russian village landscape wooden house snow, cinematic illustration",
            model="flux",
            width=width,
            height=height,
        )
    if not data:
        if not is_valid_pollinations_key(settings.POLLINATIONS_API_KEY):
            return {
                "error": (
                    "Генератор картинок не настроен: на сервере нет POLLINATIONS_API_KEY. "
                    "Получите ключ на enter.pollinations.ai и добавьте в /opt/pgbot/.env"
                ),
            }
        fallback_id = save_fallback_image(prompt)
        if fallback_id:
            return {
                "url": f"/api/v1/ai/images/{fallback_id}",
                "model": model,
                "prompt": prompt,
                "provider": "local-poster",
            }
        return {"error": "Не удалось сгенерировать изображение. Попробуйте упростить описание."}

    image_id = save_image(data, "jpg")
    return {
        "url": f"/api/v1/ai/images/{image_id}",
        "model": model,
        "prompt": prompt,
        "provider": "pollinations",
    }


async def _generate_gemini_image(prompt: str) -> dict | None:
    try:
        import base64

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

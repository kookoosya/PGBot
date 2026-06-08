"""Генерация изображений и список AI-моделей."""

import logging
from urllib.parse import quote

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

CHAT_MODELS = [
    {"id": "gemini-2.0-flash", "label": "Gemini 2.0 Flash", "provider": "google", "fast": True},
    {"id": "gemini-1.5-pro", "label": "Gemini 1.5 Pro", "provider": "google", "smart": True},
    {"id": "gemini-2.0-flash-lite", "label": "Gemini Flash Lite", "provider": "google", "fast": True},
]

IMAGE_MODELS = [
    {"id": "nano-banana", "label": "Nano Banana", "provider": "pollinations", "desc": "Яркие иллюстрации"},
    {"id": "flux", "label": "Flux", "provider": "pollinations", "desc": "Реалистичные фото"},
    {"id": "turbo", "label": "Turbo", "provider": "pollinations", "desc": "Быстрая генерация"},
    {"id": "gemini-imagen", "label": "Gemini Imagen", "provider": "google", "desc": "Через Google AI (нужен ключ)"},
]

POLLINATIONS_MODEL_MAP = {
    "nano-banana": "flux",
    "flux": "flux",
    "turbo": "turbo",
}


async def generate_image(prompt: str, model: str = "nano-banana", width: int = 1024, height: int = 1024) -> dict:
    """Сгенерировать картинку по описанию."""
    prompt = prompt.strip()[:500]
    if not prompt:
        return {"error": "Пустой запрос"}

    if model == "gemini-imagen" and settings.GEMINI_API_KEY:
        result = await _generate_gemini_image(prompt)
        if result:
            return result

    poll_model = POLLINATIONS_MODEL_MAP.get(model, "flux")
    url = (
        f"https://image.pollinations.ai/prompt/{quote(prompt)}"
        f"?model={poll_model}&width={width}&height={height}&nologo=true"
    )
    try:
        async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image"):
                return {
                    "url": str(resp.url),
                    "model": model,
                    "prompt": prompt,
                    "provider": "pollinations",
                }
    except Exception as exc:
        logger.error("Image generation failed: %s", exc)

    return {"error": "Не удалось сгенерировать изображение. Попробуйте другую модель."}


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
                import base64
                mime = part.inline_data.mime_type or "image/png"
                b64 = base64.b64encode(part.inline_data.data).decode()
                return {
                    "url": f"data:{mime};base64,{b64}",
                    "model": "gemini-imagen",
                    "prompt": prompt,
                    "provider": "google",
                }
    except Exception as exc:
        logger.warning("Gemini image gen unavailable: %s", exc)
    return None

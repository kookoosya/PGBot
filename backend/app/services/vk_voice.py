"""Распознавание голосовых сообщений VK."""

import logging

import httpx

from app.config import get_settings
from app.services.ai_status import is_valid_gemini_key

logger = logging.getLogger(__name__)
settings = get_settings()


def extract_audio_url(attachments: list[dict]) -> str | None:
    for att in attachments:
        if att.get("type") != "audio_message":
            continue
        audio = att.get("audio_message", {})
        return audio.get("link_ogg") or audio.get("link_mp3")
    return None


async def transcribe_audio_url(url: str) -> str | None:
    if not is_valid_gemini_key(settings.GEMINI_API_KEY):
        return None
    try:
        import google.generativeai as genai

        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return None
            audio_bytes = resp.content

        mime = "audio/ogg" if ".ogg" in url.lower() else "audio/mpeg"
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        result = model.generate_content([
            "Распознай голосовое сообщение на русском. Верни только текст без пояснений.",
            {"mime_type": mime, "data": audio_bytes},
        ])
        text = (result.text or "").strip()
        return text if len(text) >= 3 else None
    except Exception as exc:
        logger.warning("Voice transcription failed: %s", exc)
        return None

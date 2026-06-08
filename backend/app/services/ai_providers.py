"""Резервные AI-провайдеры (Pollinations gen API)."""

import logging
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

POLLINATIONS_TEXT_URL = "https://gen.pollinations.ai/text"
POLLINATIONS_IMAGE_URL = "https://gen.pollinations.ai/image"


async def pollinations_text(prompt: str, timeout: float = 90.0) -> str | None:
    """Текст через gen.pollinations.ai (без ключа)."""
    text = prompt.strip()[:4000]
    if not text:
        return None
    url = f"{POLLINATIONS_TEXT_URL}/{quote(text)}"
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and resp.text.strip():
                return resp.text.strip()
    except Exception as exc:
        logger.warning("Pollinations text failed: %s", exc)
    return None


async def pollinations_image_bytes(
    prompt: str,
    model: str = "flux",
    width: int = 1024,
    height: int = 1024,
    timeout: float = 120.0,
) -> bytes | None:
    """Скачать картинку с gen.pollinations.ai."""
    text = prompt.strip()[:500]
    if not text:
        return None
    url = (
        f"{POLLINATIONS_IMAGE_URL}/{quote(text)}"
        f"?model={model}&width={width}&height={height}&nologo=true&enhance=true"
    )
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url)
            ctype = resp.headers.get("content-type", "")
            if resp.status_code == 200 and ctype.startswith("image/"):
                return resp.content
            logger.warning("Pollinations image HTTP %s ctype=%s", resp.status_code, ctype)
    except Exception as exc:
        logger.error("Pollinations image failed: %s", exc)
    return None

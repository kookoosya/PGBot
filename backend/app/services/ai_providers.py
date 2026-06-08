"""Резервные AI-провайдеры (Pollinations gen API)."""

import logging
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

POLLINATIONS_TEXT_URL = "https://gen.pollinations.ai/text"
POLLINATIONS_IMAGE_URL = "https://gen.pollinations.ai/image"


async def pollinations_text(prompt: str, timeout: float = 90.0) -> str | None:
    """Короткий запрос через Pollinations (с VPS работают только простые фразы)."""
    text = prompt.strip()[:4000]
    if not text:
        return None

    # Извлекаем суть — длинный system prompt API отклоняет
    user_part = text
    if "Пользователь:" in text:
        user_part = text.rsplit("Пользователь:", 1)[-1].split("Ассистент:")[0].strip()
    short = f"Answer in Russian helpfully: {user_part[:280]}"

    for candidate in (short, user_part[:120]):
        if len(candidate) < 8:
            continue
        for base in (POLLINATIONS_TEXT_URL, "https://text.pollinations.ai"):
            url = f"{base}/{quote(candidate)}"
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    resp = await client.get(url)
                    body = resp.text.strip()
                    if resp.status_code == 200 and body and not body.startswith("{"):
                        return body
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

"""Внешние AI API: Pollinations, OpenRouter."""

import base64
import logging
import re
from urllib.parse import quote

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

POLLINATIONS_BASE = "https://gen.pollinations.ai"
POLLINATIONS_TEXT_URL = f"{POLLINATIONS_BASE}/text"
POLLINATIONS_IMAGE_URL = f"{POLLINATIONS_BASE}/image"
POLLINATIONS_CHAT_URL = f"{POLLINATIONS_BASE}/v1/chat/completions"

POLLINATIONS_CHAT_MODELS = {
    "gemini-flash": "gemini-3.5-flash",
    "gemini": "gemini",
    "openai-fast": "openai-fast",
    "openai": "openai",
    "pollinations": "gemini-3.5-flash",
    "gemini-2.0-flash": "gemini-3.5-flash",
    "gemini-1.5-pro": "gemini",
}

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

OPENROUTER_CHAT_MODELS = {
    "gemini-flash": "openai/gpt-4o-mini",
    "openai-fast": "openai/gpt-4o-mini",
    "openai": "openai/gpt-4o",
    "gemini": "openai/gpt-4o",
    "gemini-2.0-flash": "openai/gpt-4o-mini",
    "gemini-1.5-pro": "openai/gpt-4o",
}

OPENROUTER_IMAGE_MODELS = {
    "flux": "google/gemini-2.5-flash-image",
    "turbo": "google/gemini-2.5-flash-image",
    "nanobanana": "google/gemini-2.5-flash-image",
    "gemini-image": "google/gemini-2.5-flash-image",
}


def _pollinations_key() -> str:
    return settings.POLLINATIONS_API_KEY.strip()


def _pollinations_headers() -> dict[str, str]:
    key = _pollinations_key()
    if not key:
        return {}
    # sk_/pk_ — Bearer; ключи AQ.* надёжнее только через ?key=
    if key.startswith(("sk_", "pk_")):
        return {"Authorization": f"Bearer {key}"}
    return {}


def _pollinations_key_query() -> str:
    key = _pollinations_key()
    return f"?key={quote(key)}" if key else ""


def _pollinations_key_param() -> str:
    key = _pollinations_key()
    return f"&key={quote(key)}" if key else ""


async def pollinations_chat(
    message: str,
    history: list[dict] | None,
    system_prompt: str,
    model_id: str = "gemini-flash",
    timeout: float = 120.0,
) -> str | None:
    """OpenAI-совместимый чат через Pollinations."""
    if not settings.POLLINATIONS_API_KEY.strip():
        return None

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history[-8:]:
            role = msg.get("role", "user")
            if role not in ("user", "assistant"):
                continue
            openai_role = "assistant" if role == "assistant" else "user"
            content = (msg.get("content") or "")[:2000]
            if content:
                messages.append({"role": openai_role, "content": content})
    messages.append({"role": "user", "content": message[:2000]})

    poll_model = POLLINATIONS_CHAT_MODELS.get(model_id, model_id)

    chat_url = f"{POLLINATIONS_CHAT_URL}{_pollinations_key_query()}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                chat_url,
                headers={**_pollinations_headers(), "Content-Type": "application/json"},
                json={"model": poll_model, "messages": messages, "max_tokens": 1800},
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                return text.strip() if text else None
            logger.warning("Pollinations chat HTTP %s: %s", resp.status_code, resp.text[:300])
    except Exception as exc:
        logger.error("Pollinations chat failed: %s", exc)
    return None


async def pollinations_text(prompt: str, timeout: float = 90.0) -> str | None:
    """Простой GET-текст (резерв, если chat completions недоступен)."""
    if not settings.POLLINATIONS_API_KEY.strip():
        return None

    text = prompt.strip()[:4000]
    if not text:
        return None

    user_part = text
    if "Пользователь:" in text:
        user_part = text.rsplit("Пользователь:", 1)[-1].split("Ассистент:")[0].strip()
    short = f"Answer in Russian helpfully and thoroughly: {user_part[:500]}"

    key_q = _pollinations_key_param()
    headers = _pollinations_headers()

    for candidate in (short, user_part[:200]):
        if len(candidate) < 8:
            continue
        url = f"{POLLINATIONS_TEXT_URL}/{quote(candidate)}?{key_q.lstrip('&')}"
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
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

    key_q = _pollinations_key_param()
    headers = _pollinations_headers()
    urls = [
        (
            f"{POLLINATIONS_IMAGE_URL}/{quote(text)}"
            f"?model={model}&width={width}&height={height}&nologo=true&enhance=true{key_q}"
        ),
        (
            f"https://image.pollinations.ai/prompt/{quote(text)}"
            f"?model={model}&width={width}&height={height}&nologo=true{key_q}"
        ),
    ]

    for url in urls:
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                ctype = resp.headers.get("content-type", "")
                if resp.status_code == 200 and ctype.startswith("image/"):
                    return resp.content
                logger.warning("Pollinations image HTTP %s ctype=%s", resp.status_code, ctype)
        except Exception as exc:
            logger.error("Pollinations image failed: %s", exc)
    return None


def _openrouter_headers() -> dict[str, str]:
    key = settings.OPENROUTER_API_KEY.strip()
    if not key:
        return {}
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.PUBLIC_SITE_URL or "https://pushkinskie-gory.ru",
        "X-Title": "Pushkinskie Gory Portal",
    }


async def openrouter_chat(
    message: str,
    history: list[dict] | None,
    system_prompt: str,
    model_id: str = "gemini-flash",
    timeout: float = 120.0,
) -> str | None:
    if not settings.OPENROUTER_API_KEY.strip():
        return None

    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if history:
        for msg in history[-8:]:
            role = msg.get("role", "user")
            if role not in ("user", "assistant"):
                continue
            openai_role = "assistant" if role == "assistant" else "user"
            content = (msg.get("content") or "")[:2000]
            if content:
                messages.append({"role": openai_role, "content": content})
    messages.append({"role": "user", "content": message[:2000]})

    or_model = OPENROUTER_CHAT_MODELS.get(model_id, "openai/gpt-4o-mini")

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers=_openrouter_headers(),
                json={"model": or_model, "messages": messages, "max_tokens": 1800},
            )
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                return text.strip() if text else None
            logger.warning("OpenRouter chat HTTP %s: %s", resp.status_code, resp.text[:300])
    except Exception as exc:
        logger.error("OpenRouter chat failed: %s", exc)
    return None


def _decode_data_url(data_url: str) -> bytes | None:
    match = re.match(r"data:([^;]+);base64,(.+)", data_url, re.DOTALL)
    if not match:
        return None
    try:
        return base64.b64decode(match.group(2))
    except Exception:
        return None


async def openrouter_image_bytes(
    prompt: str,
    model: str = "flux",
    timeout: float = 180.0,
) -> bytes | None:
    if not settings.OPENROUTER_API_KEY.strip():
        return None

    or_model = OPENROUTER_IMAGE_MODELS.get(model, "google/gemini-2.5-flash-image")
    user_prompt = f"Generate a detailed image: {prompt.strip()[:500]}"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers=_openrouter_headers(),
                json={
                    "model": or_model,
                    "messages": [{"role": "user", "content": user_prompt}],
                    "modalities": ["image", "text"],
                    "max_tokens": 1024,
                },
            )
            if resp.status_code != 200:
                logger.warning("OpenRouter image HTTP %s: %s", resp.status_code, resp.text[:300])
                return None

            data = resp.json()
            images = data.get("choices", [{}])[0].get("message", {}).get("images") or []
            for item in images:
                url = (item.get("image_url") or {}).get("url") or ""
                if url.startswith("data:"):
                    decoded = _decode_data_url(url)
                    if decoded:
                        return decoded
                if url.startswith("http"):
                    img_resp = await client.get(url)
                    if img_resp.status_code == 200:
                        return img_resp.content
    except Exception as exc:
        logger.error("OpenRouter image failed: %s", exc)
    return None

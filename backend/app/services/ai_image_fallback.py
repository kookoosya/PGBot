"""Декоративная картинка с подписью, если внешний API недоступен."""

import io
import textwrap

from app.services.ai_image_store import save_image

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None  # type: ignore


def _gradient(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = int(26 + (y / h) * 40)
        g = int(76 + (y / h) * 30)
        b = int(58 + (y / h) * 20)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def create_prompt_poster(prompt: str, width: int = 1024, height: int = 768) -> bytes | None:
    if Image is None:
        return None
    img = _gradient((width, height))
    draw = ImageDraw.Draw(img)
    title = "Пушкинские Горы · ИИ"
    lines = textwrap.wrap(prompt[:120], width=28) or ["Ваш запрос"]
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except OSError:
        font_lg = ImageFont.load_default()
        font_sm = font_lg

    draw.text((48, 48), title, fill=(244, 211, 94), font=font_lg)
    y = 140
    for line in lines:
        draw.text((48, y), line, fill=(240, 248, 245), font=font_sm)
        y += 32
    draw.text((48, height - 60), "🪶 Сгенерировано порталом посёлка", fill=(180, 200, 190), font=font_sm)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def save_fallback_image(prompt: str) -> str | None:
    data = create_prompt_poster(prompt)
    if not data:
        return None
    return save_image(data, "jpg")

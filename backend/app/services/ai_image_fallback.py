"""Декоративная картинка с подписью, если внешний API недоступен."""

import html
import io
import textwrap

from app.services.ai_image_store import save_image

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None  # type: ignore


def _esc(text: str) -> str:
    return html.escape(text, quote=True)


def _wrap_lines(prompt: str, width: int = 32) -> list[str]:
    lines = textwrap.wrap(prompt[:140], width=width) or ["Ваш запрос"]
    return lines[:5]


def create_svg_poster(prompt: str, width: int = 1024, height: int = 768) -> bytes:
    """SVG с кириллицей — браузер рисует шрифтами пользователя."""
    lines = _wrap_lines(prompt)
    line_ys = [300 + i * 34 for i in range(len(lines))]
    tspans = "\n".join(
        f'    <tspan x="64" y="{y}">{_esc(line)}</tspan>' for y, line in zip(line_ys, lines, strict=False)
    )

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#1a3d52"/>
      <stop offset="55%" stop-color="#2d6a4f"/>
      <stop offset="100%" stop-color="#1b4332"/>
    </linearGradient>
    <linearGradient id="hill" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#2d6a4f"/>
      <stop offset="100%" stop-color="#40916c"/>
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="3" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="url(#sky)"/>
  <circle cx="{width - 120}" cy="110" r="52" fill="#f4d35e" opacity="0.92" filter="url(#glow)"/>
  <ellipse cx="{width // 2}" cy="{height - 80}" rx="{width // 2 + 40}" ry="140" fill="url(#hill)" opacity="0.85"/>
  <rect x="180" y="360" width="200" height="130" rx="4" fill="#8b5e3c"/>
  <polygon points="160,360 280,280 400,360" fill="#5c3d2e"/>
  <rect x="248" y="420" width="48" height="70" fill="#3d2817"/>
  <rect x="210" y="390" width="36" height="36" fill="#ffe8a3" opacity="0.9"/>
  <rect x="310" y="390" width="36" height="36" fill="#ffe8a3" opacity="0.9"/>
  <polygon points="520,420 540,340 560,420" fill="#1b4332"/>
  <polygon points="600,430 630,330 660,430" fill="#2d6a4f"/>
  <polygon points="700,425 735,310 770,425" fill="#1b4332"/>
  <rect x="0" y="0" width="{width}" height="{height}" fill="url(#sky)" opacity="0.35"/>
  <text x="64" y="72" fill="#f4d35e" font-size="34" font-weight="700"
        font-family="'DejaVu Sans', 'Noto Sans', Arial, sans-serif">Пушкинские Горы · ИИ</text>
  <text fill="#f0f8f5" font-size="22" font-family="'DejaVu Sans', 'Noto Sans', Arial, sans-serif">
{tspans}
  </text>
  <text x="64" y="{height - 48}" fill="#b8d4c8" font-size="16"
        font-family="'DejaVu Sans', 'Noto Sans', Arial, sans-serif">
    Локальная иллюстрация · внешний генератор временно недоступен
  </text>
</svg>
"""
    return svg.encode("utf-8")


def _gradient(size: tuple[int, int]) -> "Image.Image":
    w, h = size
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = int(26 + (y / h) * 40)
        g = int(76 + (y / h) * 30)
        b = int(58 + (y / h) * 20)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def create_jpeg_poster(prompt: str, width: int = 1024, height: int = 768) -> bytes | None:
    """JPEG-постер, если в контейнере установлены шрифты DejaVu."""
    if Image is None:
        return None
    img = _gradient((width, height))
    draw = ImageDraw.Draw(img)
    title = "Пушкинские Горы · ИИ"
    lines = _wrap_lines(prompt)
    try:
        font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except OSError:
        return None

    draw.text((48, 48), title, fill=(244, 211, 94), font=font_lg)
    y = 140
    for line in lines:
        draw.text((48, y), line, fill=(240, 248, 245), font=font_sm)
        y += 32
    draw.text(
        (48, height - 60),
        "Локальная иллюстрация · внешний генератор недоступен",
        fill=(180, 200, 190),
        font=font_sm,
    )

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88)
    return buf.getvalue()


def save_fallback_image(prompt: str) -> str | None:
    jpeg = create_jpeg_poster(prompt)
    if jpeg:
        return save_image(jpeg, "jpg")
    svg = create_svg_poster(prompt)
    return save_image(svg, "svg")

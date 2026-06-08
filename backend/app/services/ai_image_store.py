"""Временное хранение сгенерированных картинок на нашем домене."""

import uuid
from pathlib import Path

from app.config import get_settings

settings = get_settings()
IMAGE_DIR = Path(getattr(settings, "AI_IMAGE_DIR", "/tmp/pgbot-ai-images"))


def ensure_dir() -> Path:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    return IMAGE_DIR


def save_image(data: bytes, ext: str = "jpg") -> str:
    ensure_dir()
    image_id = uuid.uuid4().hex
    path = IMAGE_DIR / f"{image_id}.{ext}"
    path.write_bytes(data)
    return image_id


def image_path(image_id: str) -> Path | None:
    ensure_dir()
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = IMAGE_DIR / f"{image_id}.{ext}"
        if p.is_file():
            return p
    return None

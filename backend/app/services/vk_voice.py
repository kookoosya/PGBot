"""Backward-compatible re-exports. Prefer ``app.services.vk.voice``."""

from app.services.vk.voice import extract_audio_url, transcribe_audio_url

__all__ = ["extract_audio_url", "transcribe_audio_url"]

"""Infer EventRegion from free text (title, location, description)."""

from __future__ import annotations

from app.models.enums import EventRegion

_PUSHKIN_MARKERS = (
    "пушкиногор",
    "пушкинские гор",
    "михайловск",
    "бугров",
    "пушкинский заповедник",
    "пушкинск",
    "святогор",
    "тригорск",
    "петровск",
    "пушкин",
)


def infer_event_region_from_text(
    text: str,
    *,
    default: EventRegion = EventRegion.PSKOV,
) -> EventRegion:
    """Classify Pushkin Gory vs Pskov from combined event text."""
    lower = text.lower()
    if any(marker in lower for marker in _PUSHKIN_MARKERS):
        return EventRegion.PUSHKIN_GORY
    return default

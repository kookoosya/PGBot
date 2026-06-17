"""Admin dashboard data for external event sources."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.services.event_source_health import build_event_sources_health
from app.services.event_sources.coordinator import list_event_sources

SOURCE_LABELS: dict[str, str] = {
    "vk": "ВКонтакте",
    "pushkinland": "Пушкинский заповедник",
    "informpskov": "ИнформПсков",
    "pln": "PLN Pskov",
    "timepad": "TimePad",
    "kdc": "КДЦ Пушкиногорье",
    "drampush": "Драматический театр",
    "kinopskov": "Kinopskov",
    "mirage": "Кинотеатр «Мираж»",
    "silver": "Кинотеатр «Серебряный век»",
    "orbilet": "Orbilet",
    "proculture": "PRO.Культура",
    "kudago": "KudaGo",
    "manual": "Вручную",
}

TOKEN_HINTS: dict[str, str] = {
    "vk": "VK_EVENTS_TOKEN в .deploy.env (docs/VK_SETUP.md, шаг 8)",
    "timepad": "TIMEPAD_API_TOKEN в .deploy.env",
    "proculture": "PROCULTURE_API_KEY в .deploy.env",
}


def _source_health(source: str, health: dict[str, str]) -> str:
    if source == "vk":
        return health["vk_wall"]
    if source == "timepad":
        return health["timepad"]
    if source == "proculture":
        return health["proculture"]
    return "ready"


def _token_hint(source: str, status: str) -> str | None:
    if status == "ready":
        return None
    return TOKEN_HINTS.get(source)


async def _published_counts_by_source(db: AsyncSession) -> dict[str, int]:
    rows = await db.execute(
        select(Event.source, func.count())
        .where(Event.is_published.is_(True))
        .group_by(Event.source),
    )
    counts: dict[str, int] = {}
    for source, count in rows.all():
        key = (source or "manual").strip() or "manual"
        counts[key] = int(count)
    return counts


async def _last_synced_by_source(db: AsyncSession) -> dict[str, object | None]:
    rows = await db.execute(
        select(Event.source, func.max(Event.updated_at)).group_by(Event.source),
    )
    synced: dict[str, object | None] = {}
    for source, updated_at in rows.all():
        key = (source or "manual").strip() or "manual"
        synced[key] = updated_at
    return synced


async def build_event_sources_overview(db: AsyncSession) -> dict:
    health = build_event_sources_health()
    counts = await _published_counts_by_source(db)
    last_synced = await _last_synced_by_source(db)
    sources = []
    for name in list_event_sources():
        status = _source_health(name, health)
        sources.append(
            {
                "id": name,
                "label": SOURCE_LABELS.get(name, name),
                "health": status,
                "published_count": counts.get(name, 0),
                "token_hint": _token_hint(name, status),
                "last_synced_at": last_synced.get(name),
            },
        )
    manual_count = counts.get("manual", 0)
    if manual_count:
        sources.append(
            {
                "id": "manual",
                "label": SOURCE_LABELS["manual"],
                "health": "ready",
                "published_count": manual_count,
                "token_hint": None,
                "last_synced_at": last_synced.get("manual"),
            },
        )
    return {
        "sources": sources,
        "total_published": sum(counts.values()),
        "event_sources_health": health,
    }

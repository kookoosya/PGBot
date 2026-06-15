"""PRO.Культура.РФ import adapter (optional apiKey)."""

from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.enums import EventRegion
from app.services.event_sources.base import EventSource, EventSyncResult, FetchedEvent
from app.services.event_sources.upsert import upsert_fetched_event
from app.services.proculture_service import fetch_proculture_events, proculture_item_to_fields

logger = logging.getLogger(__name__)


class ProCultureEventSource(EventSource):
    name = "proculture"

    async def fetch_events(self, region: EventRegion | None = None) -> list[FetchedEvent]:
        if not (get_settings().PROCULTURE_API_KEY or "").strip():
            return []
        events: list[FetchedEvent] = []
        for item in await fetch_proculture_events():
            fields = proculture_item_to_fields(item)
            if not fields:
                continue
            if region is not None and fields["region"] != region:
                continue
            events.append(
                FetchedEvent(
                    title=fields["title"],
                    description=fields["description"],
                    starts_at=fields["starts_at"],
                    ends_at=fields["starts_at"] + timedelta(hours=2),
                    location=fields["location"],
                    region=fields["region"],
                    category=fields["category"],
                    source="proculture",
                    source_url=fields["source_url"],
                    genre=fields["genre"],
                )
            )
        return events

    async def sync_events(
        self,
        db: AsyncSession,
        *,
        region: EventRegion | None = None,
        actor_id: int | None = None,
    ) -> list[EventSyncResult]:
        if not (get_settings().PROCULTURE_API_KEY or "").strip():
            return [EventSyncResult(
                source="proculture",
                region=region.value if region else "all",
                fetched=0,
                created=0,
                updated=0,
                skipped=0,
                errors=["PRO.Культура: укажите PROCULTURE_API_KEY (заявка на partners@team.culture.ru)"],
            )]

        errors: list[str] = []
        created = updated = skipped = 0
        raw = await fetch_proculture_events()

        for item in raw:
            try:
                fields = proculture_item_to_fields(item)
                if not fields:
                    skipped += 1
                    continue
                if region is not None and fields["region"] != region:
                    skipped += 1
                    continue
                fetched = FetchedEvent(
                    title=fields["title"],
                    description=fields["description"],
                    starts_at=fields["starts_at"],
                    ends_at=fields["starts_at"] + timedelta(hours=2),
                    location=fields["location"],
                    region=fields["region"],
                    category=fields["category"],
                    source="proculture",
                    source_url=fields["source_url"],
                    genre=fields["genre"],
                )
                action = await upsert_fetched_event(db, fetched, actor_id=actor_id)
                if action == "created":
                    created += 1
                elif action == "updated":
                    updated += 1
                else:
                    skipped += 1
            except Exception as exc:
                logger.exception("PRO.Культура import failed for %s", item.get("_id"))
                errors.append(str(exc))

        return [EventSyncResult(
            source="proculture",
            region=region.value if region else "all",
            fetched=len(raw),
            created=created,
            updated=updated,
            skipped=skipped,
            errors=errors,
        )]

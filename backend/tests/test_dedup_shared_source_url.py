"""Dedup when multiple performances share one program page URL."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from app.models.enums import EventRegion
from app.services.event_sources.dedup import find_existing_event
from tests.helpers.db_factories import create_event

pytestmark = pytest.mark.postgres

MOSCOW = ZoneInfo("Europe/Moscow")
PROGRAM_URL = "https://pushkinland.ru/2018/news/news26/news57.php"


@pytest.mark.asyncio
async def test_shared_source_url_does_not_collapse_different_shows(db_session):
    parent = await create_event(
        db_session,
        title="Всероссийский театральный фестиваль «Бугровский гарнец»",
        source="pushkinland",
        source_url=PROGRAM_URL,
        starts_at=datetime(2026, 6, 19, 10, 0, tzinfo=MOSCOW),
        region=EventRegion.PUSHKIN_GORY,
        location="Бугрово, Пушкинские Горы",
    )
    show = await create_event(
        db_session,
        title="«Рассказы Девицы К. И. Т. » — Бугровский гарнец",
        source="pushkinland",
        source_url=PROGRAM_URL,
        starts_at=datetime(2026, 6, 19, 10, 15, tzinfo=MOSCOW),
        region=EventRegion.PUSHKIN_GORY,
        location="Бугрово, Пушкинские Горы",
    )

    match_parent = await find_existing_event(
        db_session,
        source_url=PROGRAM_URL,
        title=parent.title,
        starts_at=parent.starts_at,
        region=EventRegion.PUSHKIN_GORY.value,
        location=parent.location,
    )
    match_show = await find_existing_event(
        db_session,
        source_url=PROGRAM_URL,
        title=show.title,
        starts_at=show.starts_at,
        region=EventRegion.PUSHKIN_GORY.value,
        location=show.location,
    )

    assert match_parent and match_parent.id == parent.id
    assert match_show and match_show.id == show.id

@pytest.mark.asyncio
async def test_new_show_with_shared_url_returns_none(db_session):
    await create_event(
        db_session,
        title="Всероссийский театральный фестиваль «Бугровский гарнец»",
        source="pushkinland",
        source_url=PROGRAM_URL,
        starts_at=datetime(2026, 6, 19, 10, 0, tzinfo=MOSCOW),
        region=EventRegion.PUSHKIN_GORY,
    )

    missing = await find_existing_event(
        db_session,
        source_url=PROGRAM_URL,
        title="«Пиратские анекдоты» — Бугровский гарнец",
        starts_at=datetime(2026, 6, 20, 10, 15, tzinfo=MOSCOW),
        region=EventRegion.PUSHKIN_GORY.value,
        location="Бугрово, Пушкинские Горы",
    )
    assert missing is None

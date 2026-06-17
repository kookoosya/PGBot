"""Admin event list filters."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EventRegion, UserRole
from app.services.event.admin import list_events_admin
from tests.helpers.db_factories import auth_headers_for, create_event, create_owner_user

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_list_events_admin_filters_by_source(db_session: AsyncSession):
    await create_event(
        db_session,
        title="VK concert",
        source="vk",
        region=EventRegion.PUSHKIN_GORY,
    )
    await create_event(
        db_session,
        title="Garnect show",
        source="pushkinland",
        region=EventRegion.PUSHKIN_GORY,
    )

    vk_only = await list_events_admin(db_session, source="vk", limit=50)
    assert len(vk_only) == 1
    assert vk_only[0].source == "vk"


@pytest.mark.asyncio
async def test_admin_events_api_source_filter(api_client: AsyncClient, db_session: AsyncSession):
    owner = await create_owner_user(db_session)
    await create_event(
        db_session,
        title="PLN item",
        source="pln",
        region=EventRegion.PSKOV,
    )

    response = await api_client.get(
        "/api/v1/admin/events",
        params={"source": "pln"},
        headers=auth_headers_for(owner),
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert all(item["source"] == "pln" for item in items)

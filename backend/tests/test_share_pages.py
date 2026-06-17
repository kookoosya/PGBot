"""Share landing pages for social crawlers."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_share_garnect_page(client: AsyncClient):
    response = await client.get("/share/festival/garnect")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "og:title" in body
    assert "Бугровский гарнец" in body
    assert "/events?festival=garnect" in body


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_share_event_page(api_client: AsyncClient, db_session):
    from tests.helpers.db_factories import create_event

    event = await create_event(db_session, title="Тестовый спектакль", source="manual")
    response = await api_client.get(f"/share/events/{event.id}")
    assert response.status_code == 200
    assert "og:title" in response.text
    assert "Тестовый спектакль" in response.text
    assert f"/events/{event.id}" in response.text


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_share_event_not_found(api_client: AsyncClient):
    response = await api_client.get("/share/events/999999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_event_sources_shape(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    sources = response.json()["event_sources"]
    assert sources["timepad"] in ("ready", "needs_token")
    assert sources["proculture"] in ("ready", "needs_token")

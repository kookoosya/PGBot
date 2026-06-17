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


@pytest.mark.asyncio
async def test_health_event_sources_shape(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    sources = response.json()["event_sources"]
    assert sources["timepad"] in ("ready", "needs_token")
    assert sources["proculture"] in ("ready", "needs_token")

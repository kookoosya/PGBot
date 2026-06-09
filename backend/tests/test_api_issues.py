"""Интеграционные тесты issues API."""

import pytest
from app.models.enums import IssueStatus
from httpx import AsyncClient

from tests.conftest import API_PREFIX

pytestmark = pytest.mark.asyncio


async def test_create_and_list_my_issues(client: AsyncClient, resident_user, resident_headers):
    create = await client.post(
        f"{API_PREFIX}/issues",
        headers=resident_headers,
        json={
            "description": "Не работает уличное освещение на ул. Ленина, дом 5",
            "address": "ул. Ленина, 5",
            "category": "utilities",
        },
    )
    assert create.status_code == 201
    issue = create.json()
    assert issue["description"].startswith("Не работает")
    assert issue["status"] == IssueStatus.NEW.value
    assert issue["resident_id"] == resident_user.id

    listing = await client.get(f"{API_PREFIX}/issues", headers=resident_headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] >= 1
    ids = [item["id"] for item in body["items"]]
    assert issue["id"] in ids


async def test_official_updates_issue_status(client: AsyncClient, resident_headers, official_headers):
    create = await client.post(
        f"{API_PREFIX}/issues",
        headers=resident_headers,
        json={
            "description": "Протечка водопровода во дворе, требуется ремонт",
            "address": "ул. Пушкина, 10",
            "category": "water",
        },
    )
    assert create.status_code == 201
    issue_id = create.json()["id"]

    update = await client.patch(
        f"{API_PREFIX}/issues/{issue_id}/status",
        headers=official_headers,
        json={"status": IssueStatus.IN_PROGRESS.value, "resolution_text": "Бригада выехала"},
    )
    assert update.status_code == 200
    updated = update.json()
    assert updated["status"] == IssueStatus.IN_PROGRESS.value
    assert updated["resolution_text"] == "Бригада выехала"

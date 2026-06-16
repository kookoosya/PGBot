"""End-to-end scenario tests for critical user journeys."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ClassifiedCategory, ClassifiedPaymentStatus, EventRegion, IssueStatus, UserRole
from app.services.classified.schemas import ClassifiedActorContext, ClassifiedCreateInput, ClassifiedSearchParams
from app.services.classified_service import (
    create_classified_ad,
    moderate_classified_ad,
    search_classifieds,
)
from app.schemas.analysis_result import AnalysisResult
from app.services.event_service import search_public_events
from app.services.issue_service import IssueActorContext, apply_issue_status_update, build_my_issues_response
from tests.helpers.db_factories import (
    TEST_PASSWORD,
    auth_headers_for,
    create_event,
    create_issue,
    create_owner_user,
    create_user,
    unique_username,
)

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_auth_register_login_and_me(api_client: AsyncClient):
    username = unique_username("resident")
    password = TEST_PASSWORD

    register = await api_client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": "Иван Житель",
            "phone": "+79001234567",
        },
    )
    assert register.status_code == 201
    assert register.json()["username"] == username

    bad_login = await api_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "Wrongpass1"},
    )
    assert bad_login.status_code == 401

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await api_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me.status_code == 200
    assert me.json()["full_name"] == "Иван Житель"


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_classified_create_approve_and_publish(
    _notify_subs,
    _notify_owner,
    db_session: AsyncSession,
):
    owner = await create_owner_user(db_session)
    data = ClassifiedCreateInput(
        category=ClassifiedCategory.FIREWOOD,
        title="Дрова берёзовые колотые",
        description="Сухие дрова, доставка по посёлку, без предоплаты",
        phone="+79007654321",
        author_name="Продавец",
        agree_rules=True,
    )

    created = await create_classified_ad(db_session, data)
    assert created.ad.payment_status == ClassifiedPaymentStatus.PENDING
    assert created.ad.is_active is False

    actor = ClassifiedActorContext(actor_id=owner.id)
    moderated = await moderate_classified_ad(
        db_session,
        created.ad.id,
        action="approve",
        actor=actor,
    )
    assert moderated.ad.payment_status == ClassifiedPaymentStatus.APPROVED
    assert moderated.ad.is_active is True

    published = await search_classifieds(
        db_session,
        ClassifiedSearchParams(
            search="берёзовые",
            payment_status=ClassifiedPaymentStatus.APPROVED,
            is_active=True,
            page_size=20,
        ),
    )
    assert any(item.id == created.ad.id for item in published.items)


@pytest.mark.asyncio
@patch("app.services.issue.status.safe_notify_status", new_callable=AsyncMock, return_value=True)
async def test_resident_sees_issue_status_after_official_update(
    _notify,
    db_session: AsyncSession,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Житель")
    official = await create_user(db_session, role_name=UserRole.ADMINISTRATION)
    issue = await create_issue(db_session, resident=resident)

    await apply_issue_status_update(
        db_session,
        issue,
        status=IssueStatus.UNDER_REVIEW,
        resolution_text=None,
        actor=IssueActorContext(actor_id=official.id),
    )
    await apply_issue_status_update(
        db_session,
        issue,
        status=IssueStatus.RESOLVED,
        resolution_text="Проблема устранена",
        actor=IssueActorContext(actor_id=official.id),
    )

    response = await build_my_issues_response(db_session, resident, limit=10)
    mine = next(item for item in response.items if item.id == issue.id)
    assert mine.status == IssueStatus.RESOLVED
    assert mine.status_timeline
    assert mine.status_timeline[-1].status == IssueStatus.RESOLVED.value


@pytest.mark.asyncio
@patch("app.services.issue_processor.process_web_complaint", new_callable=AsyncMock)
async def test_guest_submits_issue_via_http(mock_process, api_client: AsyncClient):
    mock_issue = MagicMock()
    mock_issue.is_spam = False
    mock_issue.id = 501
    mock_issue.status = IssueStatus.NEW
    mock_issue.description = "Сломан фонарь на улице"
    mock_issue.resident_id = None
    mock_process.return_value = mock_issue

    with patch("app.services.issue_service.get_issue_details", new_callable=AsyncMock, return_value=mock_issue):
        response = await api_client.post(
            "/api/v1/issues",
            json={
                "description": "Сломан фонарь на улице Ленина, темно по вечерам",
                "phone": "+79001112233",
                "full_name": "Гость",
            },
        )
    assert response.status_code == 201
    assert response.json()["id"] == 501


@pytest.mark.asyncio
async def test_public_events_region_filter(db_session: AsyncSession, api_client: AsyncClient):
    pushkin = await create_event(db_session, title="Концерт в Пушкинских Горах", region=EventRegion.PUSHKIN_GORY)
    await create_event(db_session, title="Концерт в Пскове", region=EventRegion.PSKOV)

    local = await search_public_events(db_session, region=EventRegion.PUSHKIN_GORY, limit=50)
    titles = {event.title for event in local}
    assert pushkin.title in titles
    assert "Концерт в Пскове" not in titles

    http = await api_client.get("/api/v1/public/events", params={"region": "pushkin_gory"})
    assert http.status_code == 200
    http_titles = {item["title"] for item in http.json()["items"]}
    assert pushkin.title in http_titles


@pytest.mark.asyncio
async def test_resident_lists_own_issues_via_http(db_session: AsyncSession, api_client: AsyncClient):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT)
    await create_issue(db_session, resident=resident, description="Просьба починить скамейку у школы")

    response = await api_client.get(
        "/api/v1/issues/my",
        headers=auth_headers_for(resident),
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1
    assert any("скамейку" in item["description"] for item in response.json()["items"])


@pytest.mark.asyncio
@patch("app.services.issue.status.safe_notify_status", new_callable=AsyncMock, return_value=True)
async def test_issue_timeline_via_http_after_status_change(
    _notify,
    db_session: AsyncSession,
    api_client: AsyncClient,
):
    resident = await create_user(db_session, role_name=UserRole.RESIDENT, full_name="Житель")
    official = await create_user(db_session, role_name=UserRole.ADMINISTRATION, full_name="Служба")
    issue = await create_issue(db_session, resident=resident)

    status_update = await api_client.patch(
        f"/api/v1/issues/{issue.id}/status",
        headers=auth_headers_for(official),
        json={"status": "under_review"},
    )
    assert status_update.status_code == 200

    resolved = await api_client.patch(
        f"/api/v1/issues/{issue.id}/status",
        headers=auth_headers_for(official),
        json={"status": "resolved", "resolution_text": "Фонарь заменён"},
    )
    assert resolved.status_code == 200

    mine = await api_client.get("/api/v1/issues/my", headers=auth_headers_for(resident))
    assert mine.status_code == 200
    item = next(row for row in mine.json()["items"] if row["id"] == issue.id)
    assert item["status"] == "resolved"
    assert item["status_timeline"]
    assert item["status_timeline"][-1]["status"] == "resolved"


@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
async def test_register_login_create_issue_e2e(
    mock_gemini,
    _notify_owner,
    api_client: AsyncClient,
):
    username = unique_username("issue_author")
    password = TEST_PASSWORD

    register = await api_client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": "Автор обращения",
            "phone": "+79009998877",
        },
    )
    assert register.status_code == 201

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    mock_gemini.return_value = AnalysisResult(
        is_valid=True,
        category="roads",
        summary="Сломан фонарь",
        duplicate_probability=0.0,
    )

    created = await api_client.post(
        "/api/v1/issues",
        headers=headers,
        json={"description": "Сломан фонарь на улице Ленина, темно по вечерам"},
    )
    assert created.status_code == 201
    issue_id = created.json()["id"]

    mine = await api_client.get("/api/v1/issues/my", headers=headers)
    assert mine.status_code == 200
    assert any(item["id"] == issue_id for item in mine.json()["items"])


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_register_login_create_classified_e2e(
    _notify_subs,
    _notify_owner,
    api_client: AsyncClient,
):
    username = unique_username("seller")
    password = TEST_PASSWORD

    register = await api_client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": "Продавец",
            "phone": "+79006665544",
        },
    )
    assert register.status_code == 201

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = await api_client.post(
        "/api/v1/classifieds",
        headers=headers,
        json={
            "category": "firewood",
            "title": "Дрова для бани",
            "description": "Сухие берёзовые дрова, самовывоз без предоплаты",
            "phone": "+79006665544",
            "author_name": "Продавец",
            "agree_rules": True,
        },
    )
    assert created.status_code == 201
    assert created.json()["id"] > 0
    assert created.json()["message"]


@pytest.mark.asyncio
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_resident_reads_own_classifieds_in_cabinet(
    _notify_subs,
    _notify_owner,
    api_client: AsyncClient,
):
    username = unique_username("cabinet_seller")
    password = TEST_PASSWORD

    register = await api_client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": "Житель-продавец",
            "phone": "+79001239876",
        },
    )
    assert register.status_code == 201

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    created = await api_client.post(
        "/api/v1/classifieds",
        headers=headers,
        json={
            "category": "sale",
            "title": "Тумбочка деревянная",
            "description": "Тумбочка в хорошем состоянии",
            "phone": "+79001239876",
            "author_name": "Житель-продавец",
            "agree_rules": True,
        },
    )
    assert created.status_code == 201
    created_id = created.json()["id"]

    mine = await api_client.get("/api/v1/classifieds/mine", headers=headers)
    assert mine.status_code == 200
    assert any(item["id"] == created_id for item in mine.json()["items"])


@pytest.mark.asyncio
@patch("app.services.issue.ingest.notify_owner", new_callable=AsyncMock)
@patch("app.services.issue.gemini_analysis.run_gemini_with_retry", new_callable=AsyncMock)
@patch("app.services.classified.create.safe_notify_owner", new_callable=AsyncMock, return_value=True)
@patch("app.services.vk.bot.notify_subscribers_new_ad", new_callable=AsyncMock, return_value=0)
async def test_full_cabinet_journey_issues_and_classifieds(
    _notify_subs,
    _notify_owner,
    mock_gemini,
    _notify_issue_owner,
    api_client: AsyncClient,
):
    username = unique_username("cabinet_full")
    password = TEST_PASSWORD

    register = await api_client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": "Полный кабинет",
            "phone": "+79005553322",
        },
    )
    assert register.status_code == 201

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    mock_gemini.return_value = AnalysisResult(
        is_valid=True,
        category="roads",
        summary="Яма на дороге",
        duplicate_probability=0.0,
    )

    issue = await api_client.post(
        "/api/v1/issues",
        headers=headers,
        json={"description": "На улице Мира большая яма, опасно для машин"},
    )
    assert issue.status_code == 201
    issue_id = issue.json()["id"]

    classified = await api_client.post(
        "/api/v1/classifieds",
        headers=headers,
        json={
            "category": "sale",
            "title": "Детский велосипед",
            "description": "Велосипед в хорошем состоянии, самовывоз",
            "phone": "+79005553322",
            "author_name": "Полный кабинет",
            "agree_rules": True,
        },
    )
    assert classified.status_code == 201
    classified_id = classified.json()["id"]

    my_issues = await api_client.get("/api/v1/issues/my", headers=headers)
    assert my_issues.status_code == 200
    assert any(item["id"] == issue_id for item in my_issues.json()["items"])

    my_ads = await api_client.get("/api/v1/classifieds/mine", headers=headers)
    assert my_ads.status_code == 200
    ad_row = next(item for item in my_ads.json()["items"] if item["id"] == classified_id)
    assert ad_row["payment_status"] == "pending"
    assert ad_row["title"] == "Детский велосипед"

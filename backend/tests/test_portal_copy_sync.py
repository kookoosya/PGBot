"""Проверка загрузки общих текстов портала из shared/portal_copy.json."""

from app.constants import portal_copy as pc


def test_portal_copy_loads_from_shared_json():
    assert pc.BRAND_TAGLINE == "Портал посёлка"
    assert "Пушкиногорский район" in pc.BRAND_KICKER
    assert pc.ISSUE_STATUS_HINTS["NEW"]
    assert pc.ISSUE_STATUS_EMOJI["RESOLVED"] == "✅"
    assert "Объявлений пока нет" in pc.CLASSIFIED_EMPTY_VK
    assert pc.LINK_SUBMIT_COMPLAINT.startswith("✍️")


def test_issue_status_hints_match_frontend_keys():
    expected = {
        "NEW",
        "UNDER_REVIEW",
        "ASSIGNED",
        "IN_PROGRESS",
        "RESOLVED",
        "REJECTED",
        "ARCHIVED",
    }
    assert set(pc.ISSUE_STATUS_HINTS) == expected
    assert set(pc.ISSUE_STATUS_EMOJI) == expected

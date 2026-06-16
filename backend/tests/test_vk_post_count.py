"""VK post_count policy per region."""

from app.constants.event_config import VK_EVENT_GROUPS
from app.models.enums import EventRegion
from app.services.event_sources.vk_source import (
    DEFAULT_VK_POST_COUNT,
    PUSHKIN_GORY_VK_POST_COUNT,
    _post_count_for_preset,
)


def test_pushkin_gory_groups_fetch_more_posts():
    pushkin = [g for g in VK_EVENT_GROUPS if g.region == EventRegion.PUSHKIN_GORY]
    assert pushkin
    assert all(_post_count_for_preset(g) == PUSHKIN_GORY_VK_POST_COUNT for g in pushkin)


def test_pskov_groups_default_post_count():
    pskov = [g for g in VK_EVENT_GROUPS if g.region == EventRegion.PSKOV]
    assert pskov
    assert all(_post_count_for_preset(g) == DEFAULT_VK_POST_COUNT for g in pskov)

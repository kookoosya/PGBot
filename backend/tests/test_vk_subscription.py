"""Unit tests for VK subscription helpers."""

from app.models.enums import ClassifiedCategory
from app.models.vk_subscriber import VkSubscriber
from app.services.vk.subscription import (
    normalize_subscription_categories,
    subscriber_wants_category,
)


def test_normalize_subscription_all():
    key, label = normalize_subscription_categories("all")
    assert key == "all"
    assert "Все" in label or "все" in label.lower()


def test_normalize_subscription_jobs_alias():
    key, _ = normalize_subscription_categories("работа")
    assert key == "jobs"


def test_subscriber_wants_category_jobs():
    sub = VkSubscriber(peer_id=1, categories="jobs")
    assert subscriber_wants_category(sub, ClassifiedCategory.JOB_TOURISM) is True
    assert subscriber_wants_category(sub, ClassifiedCategory.OTHER) is False


def test_subscriber_wants_category_all():
    sub = VkSubscriber(peer_id=2, categories="all")
    assert subscriber_wants_category(sub, ClassifiedCategory.OTHER) is True

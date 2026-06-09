"""Internal dataclasses, errors and response mappers for classified ads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedCategory, ClassifiedPaymentStatus

ModerationAction = Literal["approve", "reject"]


class ClassifiedValidationError(Exception):
    """Business validation failure when creating or loading an ad."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class ClassifiedNotFoundError(ClassifiedValidationError):
    """Raised when a classified ad cannot be found."""

    def __init__(self, detail: str = "Объявление не найдено") -> None:
        super().__init__(detail, status_code=404)


@dataclass(frozen=True, slots=True)
class ClassifiedCreateInput:
    """Validated payload for creating a classified ad."""

    category: ClassifiedCategory
    title: str
    description: str
    phone: str
    author_name: str
    price: int | None = None
    price_unit: str | None = None
    address: str | None = None
    contact_telegram: str | None = None
    contact_vk: str | None = None
    payment_confirmed: bool = False
    payment_reference: str | None = None
    website_url: str | None = None
    agree_rules: bool = False


@dataclass(frozen=True, slots=True)
class ClassifiedActorContext:
    """Actor performing moderation."""

    actor_id: int


@dataclass(frozen=True, slots=True)
class ClassifiedSearchParams:
    """Filters for listing classified ads."""

    category: ClassifiedCategory | None = None
    search: str | None = None
    payment_status: ClassifiedPaymentStatus | None = ClassifiedPaymentStatus.APPROVED
    is_active: bool | None = True
    services_only: bool = False
    jobs_only: bool = False
    ads_only: bool = False
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class ClassifiedSearchResult:
    """Paginated classified ad search result."""

    items: list[ClassifiedAd]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True, slots=True)
class ClassifiedCreateResult:
    """Result of a successful ad submission."""

    ad: ClassifiedAd
    message: str
    free: bool


@dataclass(frozen=True, slots=True)
class ModerationResult:
    """Result of approve/reject moderation."""

    ad: ClassifiedAd
    message: str
    subscribers_notified: int = 0


@dataclass(frozen=True, slots=True)
class ClassifiedMarketingStats:
    """Marketing dashboard payload for classified ads."""

    total_ads: int
    total_views: int
    avg_views_per_ad: int
    monthly_reach_estimate: int
    placement_fee: int
    period_days: int
    category_stats: list[dict[str, Any]]
    roi_examples: list[dict[str, Any]]
    weekly_views: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        """Serialize to API response dict."""
        return {
            "total_ads": self.total_ads,
            "total_views": self.total_views,
            "avg_views_per_ad": self.avg_views_per_ad,
            "monthly_reach_estimate": self.monthly_reach_estimate,
            "placement_fee": self.placement_fee,
            "period_days": self.period_days,
            "category_stats": self.category_stats,
            "roi_examples": self.roi_examples,
            "weekly_views": self.weekly_views,
        }


def classified_to_response(ad: ClassifiedAd) -> dict[str, Any]:
    """Map a classified ad ORM row to public API response fields."""
    return {
        "id": ad.id,
        "category": ad.category,
        "category_label": CLASSIFIED_LABELS.get(ad.category, ad.category),
        "title": ad.title,
        "description": ad.description,
        "price": ad.price,
        "price_unit": ad.price_unit,
        "phone": ad.phone,
        "author_name": ad.author_name,
        "address": ad.address,
        "contact_telegram": ad.contact_telegram,
        "views_count": ad.views_count,
        "created_at": ad.created_at.isoformat(),
    }


def classified_to_pending_response(ad: ClassifiedAd) -> dict[str, Any]:
    """Map a classified ad ORM row to moderation queue response fields."""
    return {
        **classified_to_response(ad),
        "payment_status": ad.payment_status,
        "payment_reference": ad.payment_reference,
        "placement_fee": ad.placement_fee,
        "contact_vk": ad.contact_vk,
    }


def list_classified_category_options() -> list[dict[str, str]]:
    """Return category enum options for the public classifieds form."""
    return [{"value": category.value, "label": CLASSIFIED_LABELS[category]} for category in ClassifiedCategory]


def to_classified_create_input(data: Any) -> ClassifiedCreateInput:
    """Convert API schema to service-layer create input."""
    return ClassifiedCreateInput(
        category=data.category,
        title=data.title,
        description=data.description,
        phone=data.phone,
        author_name=data.author_name,
        price=data.price,
        price_unit=data.price_unit,
        address=data.address,
        contact_telegram=data.contact_telegram,
        contact_vk=data.contact_vk,
        payment_confirmed=data.payment_confirmed,
        payment_reference=data.payment_reference,
        website_url=data.website_url,
        agree_rules=data.agree_rules,
    )

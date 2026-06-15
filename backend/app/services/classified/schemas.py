"""Types and DTOs for classified ads service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

from app.models.classified import ClassifiedAd
from app.models.enums import ClassifiedCategory, ClassifiedPaymentStatus
from app.services.service_errors import ServiceError

ModerationAction = Literal["approve", "reject"]
ClassifiedSortField = Literal["created_at", "views_count", "title"]
ClassifiedSortOrder = Literal["asc", "desc"]

_SORT_COLUMNS: dict[ClassifiedSortField, Any] = {
    "created_at": ClassifiedAd.created_at,
    "views_count": ClassifiedAd.views_count,
    "title": ClassifiedAd.title,
}


@dataclass(frozen=True, slots=True)
class ClassifiedCreateInput:
    """Validated payload for creating a classified ad."""

    category: ClassifiedCategory
    title: str
    description: str
    phone: str
    author_name: str
    price: Optional[int] = None
    price_unit: Optional[str] = None
    address: Optional[str] = None
    contact_telegram: Optional[str] = None
    contact_vk: Optional[str] = None
    payment_confirmed: bool = False
    payment_reference: Optional[str] = None
    website_url: Optional[str] = None
    agree_rules: bool = False


@dataclass(frozen=True, slots=True)
class ClassifiedActorContext:
    """Actor performing moderation (audit logging)."""

    actor_id: int
    ip_address: Optional[str] = None


@dataclass(frozen=True, slots=True)
class ClassifiedSearchParams:
    """Filters for ``search_classifieds``."""

    category: Optional[ClassifiedCategory] = None
    search: Optional[str] = None
    payment_status: Optional[ClassifiedPaymentStatus] = ClassifiedPaymentStatus.APPROVED
    is_active: Optional[bool] = True
    user_id: Optional[int] = None
    phone: Optional[str] = None
    services_only: bool = False
    jobs_only: bool = False
    ads_only: bool = False
    neighbor_only: bool = False
    page: int = 1
    page_size: int = 20
    offset: Optional[int] = None
    sort_by: ClassifiedSortField = "created_at"
    sort_order: ClassifiedSortOrder = "desc"


@dataclass(frozen=True, slots=True)
class ClassifiedSearchResult:
    """Paginated classified ad search result."""

    items: list[ClassifiedAd]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    offset: int


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
    status_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
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
            "status_counts": self.status_counts,
        }


@dataclass(frozen=True, slots=True)
class ClassifiedCreateResult:
    """Result of a successful ad submission."""

    ad: ClassifiedAd
    message: str
    free: bool
    owner_notified: bool = True


@dataclass(frozen=True, slots=True)
class ModerationResult:
    """Result of approve/reject moderation."""

    ad: ClassifiedAd
    message: str
    subscribers_notified: int = 0
    vk_notified: bool = True
    audit_logged: bool = True


class ClassifiedValidationError(ServiceError):
    """Business validation failure when creating or loading an ad."""

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


class ClassifiedNotFoundError(ClassifiedValidationError):
    """Raised when a classified ad cannot be found (HTTP 404)."""

    def __init__(self, detail: str = "Объявление не найдено") -> None:
        super().__init__(detail, status_code=404)

"""Classified ads — thin facade over ``app.services.classified`` package.

Public API is unchanged; implementation lives in submodules.
"""

from app.services.classified.create import (
    create_classified_ad,
    create_classified_ad_from_vk,
)
from app.services.classified.moderation import moderate_classified_ad
from app.services.classified.quota import get_classified_quota
from app.services.classified.responses import (
    build_classified_list_response,
    classified_to_mine_response,
    classified_to_pending_response,
    classified_to_response,
    list_classified_category_options,
    to_classified_create_input,
)
from app.services.classified.schemas import (
    ClassifiedActorContext,
    ClassifiedCreateInput,
    ClassifiedCreateResult,
    ClassifiedMarketingStats,
    ClassifiedNotFoundError,
    ClassifiedSearchParams,
    ClassifiedSearchResult,
    ClassifiedSortField,
    ClassifiedSortOrder,
    ClassifiedValidationError,
    ModerationAction,
    ModerationResult,
)
from app.services.classified.search import increment_ad_views, search_classifieds
from app.services.classified.stats import build_marketing_stats

__all__ = [
    "ClassifiedActorContext",
    "ClassifiedCreateInput",
    "ClassifiedCreateResult",
    "ClassifiedMarketingStats",
    "ClassifiedNotFoundError",
    "ClassifiedSearchParams",
    "ClassifiedSearchResult",
    "ClassifiedSortField",
    "ClassifiedSortOrder",
    "ClassifiedValidationError",
    "ModerationAction",
    "ModerationResult",
    "build_classified_list_response",
    "build_marketing_stats",
    "classified_to_mine_response",
    "classified_to_pending_response",
    "classified_to_response",
    "create_classified_ad",
    "create_classified_ad_from_vk",
    "get_classified_quota",
    "increment_ad_views",
    "list_classified_category_options",
    "moderate_classified_ad",
    "search_classifieds",
    "to_classified_create_input",
]

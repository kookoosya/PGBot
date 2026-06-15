"""Search and read paths for classified ads."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classified import ClassifiedAd
from app.models.enums import (
    JOB_CLASSIFIED_CATEGORIES,
    NEIGHBOR_HELP_CATEGORIES,
    SERVICE_CLASSIFIED_CATEGORIES,
    ClassifiedPaymentStatus,
)
from app.services.classified.schemas import (
    ClassifiedNotFoundError,
    ClassifiedSearchParams,
    ClassifiedSearchResult,
    ClassifiedSortField,
    ClassifiedSortOrder,
    _SORT_COLUMNS,
)
from app.services.pagination_utils import normalize_pagination


def normalize_classified_pagination(
    *,
    page: int,
    page_size: int,
    total: int,
    offset: Optional[int] = None,
) -> tuple[int, int, int, int, bool, bool]:
    return normalize_pagination(
        page=page,
        page_size=page_size,
        total=total,
        offset=offset,
        max_page_size=100,
    )


def apply_search_sort(
    query: Any,
    *,
    sort_by: ClassifiedSortField,
    sort_order: ClassifiedSortOrder,
) -> Any:
    column = _SORT_COLUMNS.get(sort_by, ClassifiedAd.created_at)
    ordering = column.asc() if sort_order == "asc" else column.desc()
    if sort_by != "created_at":
        return query.order_by(ordering, ClassifiedAd.created_at.desc())
    return query.order_by(ordering)


async def search_classifieds(
    db: AsyncSession,
    params: ClassifiedSearchParams,
) -> ClassifiedSearchResult:
    """Search and filter classified ads with sorting and pagination."""
    query = select(ClassifiedAd)

    if params.payment_status is not None:
        query = query.where(ClassifiedAd.payment_status == params.payment_status)
    if params.is_active is not None:
        query = query.where(ClassifiedAd.is_active.is_(params.is_active))
    if params.user_id is not None:
        query = query.where(ClassifiedAd.user_id == params.user_id)
    if params.phone is not None:
        query = query.where(ClassifiedAd.phone == params.phone)
    if params.services_only:
        query = query.where(ClassifiedAd.category.in_(SERVICE_CLASSIFIED_CATEGORIES))
    if params.jobs_only:
        query = query.where(ClassifiedAd.category.in_(JOB_CLASSIFIED_CATEGORIES))
    elif params.ads_only:
        query = query.where(ClassifiedAd.category.notin_(JOB_CLASSIFIED_CATEGORIES))
    if params.neighbor_only:
        query = query.where(ClassifiedAd.category.in_(NEIGHBOR_HELP_CATEGORIES))
    if params.category is not None:
        query = query.where(ClassifiedAd.category == params.category)
    if params.search:
        pattern = f"%{params.search.strip()}%"
        query = query.where(
            ClassifiedAd.title.ilike(pattern) | ClassifiedAd.description.ilike(pattern),
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    page, offset, page_size, total_pages, has_prev, has_next = normalize_classified_pagination(
        page=params.page,
        page_size=params.page_size,
        total=total,
        offset=params.offset,
    )
    result = await db.execute(
        apply_search_sort(query, sort_by=params.sort_by, sort_order=params.sort_order)
        .offset(offset)
        .limit(page_size)
    )
    items = list(result.scalars().all())

    return ClassifiedSearchResult(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev,
        offset=offset,
    )


async def increment_ad_views(db: AsyncSession, ad_id: int) -> ClassifiedAd:
    """Increment view counter for an active, approved ad."""
    result = await db.execute(
        select(ClassifiedAd).where(
            ClassifiedAd.id == ad_id,
            ClassifiedAd.is_active.is_(True),
            ClassifiedAd.payment_status == ClassifiedPaymentStatus.APPROVED,
        )
    )
    ad = result.scalar_one_or_none()
    if ad is None:
        raise ClassifiedNotFoundError()

    ad.views_count += 1
    return ad

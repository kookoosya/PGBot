"""Place complaints — create, deduplication and owner notification."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import (
    MAP_REPORT_LABELS,
    SHOP_COMPLAINT_LABELS,
    IssueCategory,
    IssueStatus,
    Priority,
)
from app.models.issue import Issue
from app.models.place import PlaceComplaint
from app.models.user import User
from app.services.notify_utils import safe_notify_owner

from .details import load_place
from .schemas import (
    COMPLAINT_DUPLICATE_HOURS,
    PlaceComplaintInput,
    PlaceComplaintResult,
    PlaceValidationError,
    resolve_author_name,
)

logger = logging.getLogger(__name__)


async def check_duplicate_complaint(
    db: AsyncSession,
    place_id: int,
    *,
    user_id: int | None,
    author_name: str,
) -> None:
    """Reject repeated complaints on the same place within the cooldown window."""
    since = datetime.now(timezone.utc) - timedelta(hours=COMPLAINT_DUPLICATE_HOURS)
    try:
        query = select(PlaceComplaint.id).where(
            PlaceComplaint.place_id == place_id,
            PlaceComplaint.created_at >= since,
        )
        if user_id is not None:
            query = query.where(PlaceComplaint.user_id == user_id)
        else:
            query = query.where(
                PlaceComplaint.user_id.is_(None),
                PlaceComplaint.author_name == author_name,
            )
        existing = await db.execute(query.limit(1))
        if existing.scalar_one_or_none() is not None:
            raise PlaceValidationError(
                "Вы уже отправляли жалобу на это место недавно — попробуйте позже",
                status_code=429,
            )
    except PlaceValidationError:
        raise
    except Exception:
        logger.exception(
            "Duplicate complaint check failed for place #%s (user_id=%s)",
            place_id,
            user_id,
        )
        raise


async def create_place_complaint(
    db: AsyncSession,
    place_id: int,
    data: PlaceComplaintInput,
    *,
    user: User | None = None,
) -> PlaceComplaintResult:
    """Create a complaint, linked issue and notify the site owner safely.

    Raises ``PlaceNotFoundError`` if the place is missing and
    ``PlaceValidationError`` when a duplicate complaint is detected.
    """
    place = await load_place(db, place_id)
    author_name = resolve_author_name(data.author_name, user)
    user_id = user.id if user else None

    await check_duplicate_complaint(
        db,
        place_id,
        user_id=user_id,
        author_name=author_name,
    )

    complaint = PlaceComplaint(
        place_id=place_id,
        complaint_type=data.complaint_type,
        description=data.description,
        price_tagged=data.price_tagged,
        price_charged=data.price_charged,
        receipt_info=data.receipt_info,
        author_name=author_name,
        user_id=user_id,
    )

    type_label = MAP_REPORT_LABELS.get(data.complaint_type) or SHOP_COMPLAINT_LABELS.get(
        data.complaint_type,
        data.complaint_type,
    )
    is_map_report = data.complaint_type in MAP_REPORT_LABELS
    issue_desc = (
        f"{'Ошибка на карте' if is_map_report else 'Жалоба'}: {place.name} ({place.address or ''})\n"
        f"Тип: {type_label}\n"
        f"{data.description}"
    )
    if data.price_tagged or data.price_charged:
        issue_desc += (
            f"\nЦена на ценнике: {data.price_tagged or '—'}, "
            f"на кассе: {data.price_charged or '—'}"
        )

    issue = Issue(
        title=f"{'Карта' if is_map_report else 'Жалоба'}: {place.name}",
        description=issue_desc,
        status=IssueStatus.NEW,
        category=IssueCategory.OTHER,
        priority=Priority.MEDIUM,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        resident_id=user_id,
    )

    try:
        db.add(complaint)
        place.complaint_count += 1
        db.add(issue)
        await db.flush()
        complaint.issue_id = issue.id
    except Exception:
        logger.exception(
            "Failed to persist complaint for place #%s (user_id=%s)",
            place_id,
            user_id,
        )
        raise

    owner_notified = await safe_notify_owner(
        "⚠️ Жалоба на организацию\n\n"
        f"«{place.name}» — {place.address or 'адрес не указан'}\n"
        f"{SHOP_COMPLAINT_LABELS.get(data.complaint_type, data.complaint_type)}\n"
        f"{data.description[:300]}",
        context="place_complaint",
        resource="place",
        resource_id=place_id,
    )
    if not owner_notified:
        logger.warning(
            "Place complaint #%s created for place #%s but owner was not notified",
            complaint.id,
            place_id,
        )

    logger.info(
        "Place complaint #%s created for place #%s (issue #%s, user_id=%s)",
        complaint.id,
        place_id,
        issue.id,
        user_id,
    )
    return PlaceComplaintResult(
        complaint=complaint,
        issue=issue,
        owner_notified=owner_notified,
    )

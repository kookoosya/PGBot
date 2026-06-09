"""Place complaints and linked issue creation."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MAP_REPORT_LABELS, SHOP_COMPLAINT_LABELS, IssueCategory, IssueStatus, Priority
from app.models.issue import Issue
from app.models.place import PlaceComplaint
from app.models.user import User
from app.services.notifications import notify_owner
from app.services.place.crud import load_place
from app.services.place.schemas import PlaceComplaintInput, PlaceComplaintResult, resolve_author_name


async def create_place_complaint(
    db: AsyncSession,
    place_id: int,
    data: PlaceComplaintInput,
    *,
    user: User | None = None,
) -> PlaceComplaintResult:
    """Create a complaint, linked issue and notify the site owner."""
    place = await load_place(db, place_id)
    author_name = resolve_author_name(data.author_name, user)

    complaint = PlaceComplaint(
        place_id=place_id,
        complaint_type=data.complaint_type,
        description=data.description,
        price_tagged=data.price_tagged,
        price_charged=data.price_charged,
        receipt_info=data.receipt_info,
        author_name=author_name,
        user_id=user.id if user else None,
    )
    db.add(complaint)
    place.complaint_count += 1

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
        issue_desc += f"\nЦена на ценнике: {data.price_tagged or '—'}, на кассе: {data.price_charged or '—'}"

    issue = Issue(
        title=f"{'Карта' if is_map_report else 'Жалоба'}: {place.name}",
        description=issue_desc,
        status=IssueStatus.NEW,
        category=IssueCategory.OTHER,
        priority=Priority.MEDIUM,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        resident_id=user.id if user else None,
    )
    db.add(issue)
    await db.flush()
    complaint.issue_id = issue.id

    await notify_owner(
        "⚠️ Жалоба на организацию\n\n"
        f"«{place.name}» — {place.address or 'адрес не указан'}\n"
        f"{SHOP_COMPLAINT_LABELS.get(data.complaint_type, data.complaint_type)}\n"
        f"{data.description[:300]}",
    )

    return PlaceComplaintResult(complaint=complaint)

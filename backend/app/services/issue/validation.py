"""Web form validation and issue creation."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

from .crud import get_issue_details
from .schemas import IssueValidationError


async def create_issue_from_web(
    db: AsyncSession,
    data,
    *,
    user: User | None,
):
    """Validate web form input, create issue and reject spam."""
    from app.services.issue.ingest import process_web_complaint

    if data.website_url:
        raise IssueValidationError("Не удалось отправить форму. Обновите страницу.")

    if not user and (not data.phone or not data.full_name):
        raise IssueValidationError("Укажите имя и телефон или войдите в кабинет")

    category_value = data.category.value if data.category else None
    issue = await process_web_complaint(
        db,
        data.description,
        user=user,
        phone=data.phone or (user.phone if user else None),
        full_name=data.full_name or (user.full_name if user else None),
        address=data.address,
        category=category_value,
    )

    if issue.is_spam:
        raise IssueValidationError(
            "Обращение не принято. Опишите конкретную проблему без рекламы и оскорблений."
        )

    loaded = await get_issue_details(db, issue.id)
    return loaded or issue

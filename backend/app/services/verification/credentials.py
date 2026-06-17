"""Credential uniqueness checks for verification registration."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.verification.schemas import VerificationValidationError


async def ensure_unique_credentials(db: AsyncSession, username: str, email: str | None) -> None:
    for field, value, label in [
        ("username", username, "Логин"),
        ("email", email, "Email"),
    ]:
        if not value:
            continue
        result = await db.execute(select(User).where(getattr(User, field) == value))
        if result.scalar_one_or_none():
            raise VerificationValidationError(f"{label} уже занят")

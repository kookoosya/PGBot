"""Owner approval/rejection of pending verification requests."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import VerificationStatus
from app.models.user import User
from app.schemas.verification import VerificationAction, VerificationRequestResponse
from app.services.audit import log_action
from app.services.verification.responses import verification_to_response
from app.services.verification.schemas import VerificationNotFoundError, VerificationValidationError


async def list_pending_verifications(db: AsyncSession) -> list[VerificationRequestResponse]:
    """Return users awaiting verification approval."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.role))
        .where(User.verification_status == VerificationStatus.PENDING)
        .order_by(User.created_at.desc())
    )
    return [verification_to_response(user) for user in result.scalars().all()]


async def _get_pending_user(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise VerificationNotFoundError()
    if user.verification_status != VerificationStatus.PENDING:
        raise VerificationValidationError("Заявка уже обработана")
    return user


async def approve_verification(
    db: AsyncSession,
    user_id: int,
    data: VerificationAction,
    *,
    actor_id: int,
    ip_address: str | None = None,
) -> VerificationRequestResponse:
    """Approve a pending verification request."""
    user = await _get_pending_user(db, user_id)
    user.verification_status = VerificationStatus.APPROVED
    user.is_active = True
    user.verified_at = datetime.now(timezone.utc)
    user.verified_by_id = actor_id
    if data.note:
        user.verification_note = data.note

    await log_action(
        db, "approve_verification", "user", user.id,
        user_id=actor_id, details={"note": data.note},
        ip_address=ip_address,
    )
    return verification_to_response(user)


async def reject_verification(
    db: AsyncSession,
    user_id: int,
    data: VerificationAction,
    *,
    actor_id: int,
    ip_address: str | None = None,
) -> VerificationRequestResponse:
    """Reject a pending verification request."""
    user = await _get_pending_user(db, user_id)
    user.verification_status = VerificationStatus.REJECTED
    user.is_active = False
    if data.note:
        user.verification_note = data.note

    await log_action(
        db, "reject_verification", "user", user.id,
        user_id=actor_id, details={"note": data.note},
        ip_address=ip_address,
    )
    return verification_to_response(user)

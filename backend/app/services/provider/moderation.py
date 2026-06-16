"""Provider approval workflow."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import VerificationStatus
from app.models.user import User
from app.services.notifications import notify_owner, notify_vk_user

from .crud import get_provider_by_id


async def approve_provider(db: AsyncSession, provider_id: int) -> dict:
    """Approve a pending provider and notify them."""
    provider = await get_provider_by_id(db, provider_id)
    provider.verification_status = VerificationStatus.APPROVED
    provider.is_active = True
    if provider.user_id:
        user_result = await db.execute(select(User).where(User.id == provider.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.verification_status = VerificationStatus.APPROVED
            user.is_active = True
            if user.vk_id:
                await notify_vk_user(
                    user.vk_id,
                    f"✅ Ваш профиль мастера одобрен!\n\n{provider.full_name} — теперь в каталоге услуг посёлка.",
                )
    await notify_owner(f"✅ Мастер #{provider_id} «{provider.full_name}» одобрен и опубликован.")
    return {"status": "approved"}


async def reject_provider(
    db: AsyncSession,
    provider_id: int,
    *,
    reason: str = "Не подтверждены данные",
) -> dict:
    """Reject a pending provider."""
    provider = await get_provider_by_id(db, provider_id)
    provider.verification_status = VerificationStatus.REJECTED
    provider.is_active = False
    if provider.user_id:
        user_result = await db.execute(select(User).where(User.id == provider.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            user.verification_status = VerificationStatus.REJECTED
            user.is_active = False
            if user.vk_id:
                await notify_vk_user(user.vk_id, f"❌ Заявка мастера отклонена.\n{reason}")
    await notify_owner(f"❌ Мастер #{provider_id} «{provider.full_name}» отклонён: {reason}")
    return {"status": "rejected"}

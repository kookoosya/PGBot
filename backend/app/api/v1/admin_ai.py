from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_client_ip, get_optional_user, require_owner
from app.database import get_db
from app.models.user import User
from app.schemas.ai import AIEntitlementGrantRequest
from app.services.ai_entitlement_service import grant_entitlement, list_entitlements, revoke_entitlement

router = APIRouter()


@router.get("/entitlements")
async def admin_list_ai_entitlements(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    rows = await list_entitlements(db)
    return {
        "items": [
            {
                "id": row.id,
                "user_id": row.user_id,
                "vk_id": row.vk_id,
                "web_identifier": row.web_identifier,
                "plan_id": row.plan_id,
                "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                "payment_reference": row.payment_reference,
                "payment_amount": row.payment_amount,
                "notes": row.notes,
                "is_active": row.is_active,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.post("/entitlements", status_code=201)
async def admin_grant_ai_entitlement(
    data: AIEntitlementGrantRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_owner())],
):
    try:
        entitlement = await grant_entitlement(
            db,
            plan_id=data.plan_id,
            granted_by=current_user,
            user_id=data.user_id,
            vk_id=data.vk_id,
            web_identifier=data.web_identifier,
            period_days=data.period_days,
            payment_reference=data.payment_reference,
            payment_amount=data.payment_amount,
            notes=data.notes,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "id": entitlement.id,
        "plan_id": entitlement.plan_id,
        "user_id": entitlement.user_id,
        "expires_at": entitlement.expires_at.isoformat() if entitlement.expires_at else None,
        "message": "Доступ активирован",
    }


@router.delete("/entitlements/{entitlement_id}")
async def admin_revoke_ai_entitlement(
    entitlement_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    entitlement = await revoke_entitlement(db, entitlement_id)
    if not entitlement:
        raise HTTPException(status_code=404, detail="Запись не найдена")
    await db.commit()
    return {"message": "Доступ отключён"}

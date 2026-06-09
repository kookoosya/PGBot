from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.database import get_db
from app.models.user import User
from app.schemas.ai import AIEntitlementGrantRequest, AIProviderKeyCreateRequest
from app.services.ai_entitlement_service import grant_entitlement, list_entitlements, revoke_entitlement
from app.services.ai_key_pool import (
    add_gemini_key,
    delete_gemini_key,
    list_gemini_key_rows,
    mask_api_key,
    set_gemini_key_active,
)

router = APIRouter()


def _key_row_payload(row) -> dict:
    return {
        "id": row.id,
        "provider": row.provider,
        "label": row.label,
        "masked_key": mask_api_key(row.api_key),
        "is_active": row.is_active,
        "priority": row.priority,
        "use_count": row.use_count,
        "error_count": row.error_count,
        "last_used_at": row.last_used_at.isoformat() if row.last_used_at else None,
        "last_error_at": row.last_error_at.isoformat() if row.last_error_at else None,
        "last_error": row.last_error,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@router.get("/keys")
async def admin_list_ai_keys(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    rows = await list_gemini_key_rows(db, include_inactive=True)
    return {"items": [_key_row_payload(row) for row in rows]}


@router.post("/keys", status_code=201)
async def admin_add_ai_key(
    data: AIProviderKeyCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    try:
        row = await add_gemini_key(
            db,
            api_key=data.api_key,
            label=data.label,
            priority=data.priority,
        )
        await db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"item": _key_row_payload(row), "message": "Ключ добавлен — доступен всем оплатившим"}


@router.patch("/keys/{key_id}/activate")
async def admin_activate_ai_key(
    key_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    row = await set_gemini_key_active(db, key_id, active=True)
    if not row:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    await db.commit()
    return {"item": _key_row_payload(row), "message": "Ключ включён"}


@router.patch("/keys/{key_id}/deactivate")
async def admin_deactivate_ai_key(
    key_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    row = await set_gemini_key_active(db, key_id, active=False)
    if not row:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    await db.commit()
    return {"item": _key_row_payload(row), "message": "Ключ отключён"}


@router.delete("/keys/{key_id}")
async def admin_delete_ai_key(
    key_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    deleted = await delete_gemini_key(db, key_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ключ не найден")
    await db.commit()
    return {"message": "Ключ удалён"}


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
        "message": "Доступ активирован — работает на общем пуле ключей",
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

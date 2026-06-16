from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import limiter
from app.database import get_db
from app.schemas.vk_auth import VkAuthResponse, VkSilentAuthRequest
from app.services.vk_mini_app_auth import (
    VkMiniAppAuthError,
    authenticate_vk_mini_app,
    raise_http_for_vk_auth_error,
)

router = APIRouter()
settings = get_settings()


@router.post("/auth", response_model=VkAuthResponse)
@limiter.limit("30/minute")
async def vk_mini_app_auth(
    request: Request,
    data: VkSilentAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Exchange VK Bridge silent token for portal JWT."""
    try:
        access_token, user = await authenticate_vk_mini_app(
            db,
            silent_token=data.silent_token,
            uuid=data.uuid,
        )
    except VkMiniAppAuthError as exc:
        raise_http_for_vk_auth_error(exc)

    return VkAuthResponse(access_token=access_token, user=user)


@router.post("/refresh", response_model=VkAuthResponse)
@limiter.limit("60/minute")
async def vk_mini_app_refresh(
    request: Request,
    data: VkSilentAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Re-issue JWT when access token expired (same silent token exchange)."""
    try:
        access_token, user = await authenticate_vk_mini_app(
            db,
            silent_token=data.silent_token,
            uuid=data.uuid,
        )
    except VkMiniAppAuthError as exc:
        raise_http_for_vk_auth_error(exc)

    return VkAuthResponse(access_token=access_token, user=user)

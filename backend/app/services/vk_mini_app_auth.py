"""VK Mini App silent token exchange and portal JWT issuance."""

from __future__ import annotations

import logging

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.issue_processor import get_or_create_resident
from app.services.vk.client import VK_API_URL

logger = logging.getLogger(__name__)
settings = get_settings()


class VkMiniAppAuthError(Exception):
    """VK silent token validation failed."""


async def _vk_api_with_service_token(method: str, params: dict) -> dict:
    token = settings.VK_APP_SERVICE_TOKEN.strip()
    if not token:
        raise VkMiniAppAuthError("VK Mini App service token is not configured")

    payload = {
        **params,
        "access_token": token,
        "v": settings.VK_API_VERSION,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{VK_API_URL}/{method}", data=payload)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            error = data["error"]
            logger.warning("VK Mini App API error %s: %s", error.get("error_code"), error.get("error_msg"))
            raise VkMiniAppAuthError(error.get("error_msg", "VK API error"))
        return data.get("response", {})


async def exchange_silent_token(silent_token: str, uuid: str) -> int:
    """Validate silent token via VK API and return ``vk_id``."""
    if settings.DEBUG and silent_token.startswith("dev:"):
        if not settings.VK_APP_SERVICE_TOKEN.strip():
            try:
                return int(silent_token.split(":", 1)[1])
            except (IndexError, ValueError) as exc:
                raise VkMiniAppAuthError("Invalid dev silent token") from exc

    response = await _vk_api_with_service_token(
        "auth.exchangeSilentAuthToken",
        {"token": silent_token, "uuid": uuid},
    )
    user_id = response.get("user_id")
    if not user_id:
        raise VkMiniAppAuthError("VK did not return user_id")
    return int(user_id)


async def _enrich_user_profile(vk_id: int, user) -> None:
    """Best-effort profile enrichment from VK users.get."""
    try:
        profile = await _vk_api_with_service_token(
            "users.get",
            {
                "user_ids": str(vk_id),
                "fields": "first_name,last_name",
            },
        )
    except VkMiniAppAuthError:
        return

    if not profile:
        return

    info = profile[0] if isinstance(profile, list) else profile
    first = (info.get("first_name") or "").strip()
    last = (info.get("last_name") or "").strip()
    full_name = " ".join(part for part in (first, last) if part).strip()
    if full_name:
        user.full_name = full_name


async def authenticate_vk_mini_app(
    db: AsyncSession,
    *,
    silent_token: str,
    uuid: str,
) -> tuple[str, UserResponse]:
    """Exchange VK silent token, upsert resident user and return JWT + profile."""
    vk_id = await exchange_silent_token(silent_token, uuid)
    user = await get_or_create_resident(db, vk_id)
    await _enrich_user_profile(vk_id, user)
    await db.flush()
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == user.id)
    )
    user = result.scalar_one()

    pwd_anchor = user.password_changed_at or user.created_at
    pwd_ts = int(pwd_anchor.timestamp()) if pwd_anchor else 0
    role_name = user.role.name.value if hasattr(user.role.name, "value") else user.role.name
    access_token = create_access_token({"sub": str(user.id), "role": role_name, "pwd": pwd_ts})
    return access_token, UserResponse.model_validate(user)


def raise_http_for_vk_auth_error(exc: VkMiniAppAuthError) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=str(exc),
    ) from exc

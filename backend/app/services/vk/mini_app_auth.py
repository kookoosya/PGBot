"""VK Mini App launch-params verification and JWT issuance."""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from urllib.parse import parse_qsl

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.security import create_access_token
from app.schemas.auth import Token, UserResponse
from app.services.issue.residents import get_or_create_resident
from app.services.user_service import user_to_response
from app.utils.errors import ServiceError

logger = logging.getLogger(__name__)
settings = get_settings()


class VkMiniAppAuthError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 401) -> None:
        super().__init__(detail, status_code=status_code)


def parse_launch_params(raw: str) -> dict[str, str]:
    """Parse VK launch query string into a flat dict."""
    cleaned = raw.strip().lstrip("?").lstrip("#")
    if not cleaned:
        return {}
    return {key: value for key, value in parse_qsl(cleaned, keep_blank_values=True)}


def verify_launch_sign(params: dict[str, str], secret: str) -> bool:
    """Verify VK Mini App ``sign`` per official HMAC-SHA256 scheme."""
    sign = params.get("sign")
    if not sign or not secret:
        return False
    pairs = [
        f"{key}={params[key]}"
        for key in sorted(params.keys())
        if key != "sign" and key.startswith("vk_")
    ]
    sign_string = "&".join(pairs)
    digest = hmac.new(secret.encode(), sign_string.encode(), hashlib.sha256).digest()
    computed = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return hmac.compare_digest(computed, sign)


def vk_mini_app_configured() -> bool:
    """Return True when VK Mini App credentials are set."""
    app_id = (settings.VK_APP_ID or "").strip()
    secret = (settings.VK_APP_SECRET or "").strip()
    if not app_id or not secret or secret.startswith("your-"):
        return False
    return True


async def authenticate_vk_mini_app(
    db: AsyncSession,
    *,
    launch_params: str,
) -> tuple[Token, UserResponse]:
    """Exchange signed VK launch params for a portal JWT."""
    params = parse_launch_params(launch_params)
    if not params:
        raise VkMiniAppAuthError("Пустые launch params")

    vk_user_id_raw = params.get("vk_user_id")
    if not vk_user_id_raw:
        raise VkMiniAppAuthError("vk_user_id не найден в launch params")

    try:
        vk_user_id = int(vk_user_id_raw)
    except ValueError as exc:
        raise VkMiniAppAuthError("Некорректный vk_user_id") from exc

    if vk_mini_app_configured():
        if not verify_launch_sign(params, settings.VK_APP_SECRET):
            raise VkMiniAppAuthError("Неверная подпись launch params")
    elif settings.VK_MINI_APP_DEV_AUTH and settings.DEBUG:
        logger.warning("VK Mini App dev auth without signature for vk_user_id=%s", vk_user_id)
    else:
        raise VkMiniAppAuthError(
            "VK Mini App не настроен. Укажите VK_APP_ID и VK_APP_SECRET.",
            status_code=503,
        )

    user = await get_or_create_resident(db, vk_user_id)
    await db.refresh(user, ["role"])

    if not user.is_active:
        raise VkMiniAppAuthError("Аккаунт отключён", status_code=403)

    role_name = user.role.name.value if hasattr(user.role.name, "value") else user.role.name
    pwd_ts = int((user.password_changed_at or user.created_at).timestamp())
    token = create_access_token({"sub": str(user.id), "role": role_name, "pwd": pwd_ts, "vk": True})
    user.last_login_at = datetime.now(timezone.utc)

    return Token(access_token=token), user_to_response(user)

from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.security import decode_access_token
from app.database import get_db
from app.models.enums import UserRole
from app.models.user import User

security = HTTPBearer(auto_error=False)

ROLE_HIERARCHY = {
    UserRole.RESIDENT: 0,
    UserRole.MODERATOR: 1,
    UserRole.SOCIAL_SERVICE: 2,
    UserRole.ADMINISTRATION: 3,
    UserRole.SUPER_ADMIN: 4,
}


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account locked")

    token_pwd = payload.get("pwd")
    pwd_anchor = user.password_changed_at or user.created_at
    if pwd_anchor:
        user_pwd_ts = int(pwd_anchor.timestamp())
        if not token_pwd or int(token_pwd) < user_pwd_ts:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    return user


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_owner():
    """Only the site owner (super_admin + configured username) may access."""

    async def owner_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        settings = get_settings()
        if current_user.role.name != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Личная панель только для владельца сайта",
            )
        if current_user.username not in settings.owner_usernames:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Личная панель только для владельца сайта",
            )
        return current_user

    return owner_checker


def require_roles(*roles: UserRole):
    async def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role.name not in roles:
            min_required = min(ROLE_HIERARCHY[r] for r in roles)
            user_level = ROLE_HIERARCHY.get(current_user.role.name, -1)
            if user_level < min_required:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return role_checker


def get_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None

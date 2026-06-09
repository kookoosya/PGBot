"""Выдача, ротация и отзыв refresh-токенов."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.auth_cookies import AuthClient
from app.core.security import create_access_token
from app.models.refresh_token import RefreshToken
from app.models.user import User

settings = get_settings()


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def build_access_token(user: User) -> str:
    pwd_ts = int((user.password_changed_at or user.created_at).timestamp())
    role_name = user.role.name.value if hasattr(user.role.name, "value") else user.role.name
    return create_access_token({"sub": str(user.id), "role": role_name, "pwd": pwd_ts})


async def issue_refresh_token(db: AsyncSession, user: User, client: AuthClient) -> str:
    raw = secrets.token_urlsafe(48)
    row = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw),
        client_scope=client,
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(row)
    await db.flush()
    return raw


async def revoke_refresh_token(db: AsyncSession, raw: str, client: AuthClient) -> None:
    token_hash = hash_refresh_token(raw)
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.client_scope == client,
            RefreshToken.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(UTC))
    )


async def revoke_all_for_user(db: AsyncSession, user_id: int) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


async def get_valid_refresh_token(db: AsyncSession, raw: str, client: AuthClient) -> RefreshToken | None:
    token_hash = hash_refresh_token(raw)
    result = await db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user).selectinload(User.role))
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.client_scope == client,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    return result.scalar_one_or_none()


async def rotate_refresh_token(db: AsyncSession, row: RefreshToken) -> tuple[str, User]:
    row.revoked_at = datetime.now(UTC)
    user = row.user
    new_raw = await issue_refresh_token(db, user, row.client_scope)  # type: ignore[arg-type]
    return new_raw, user

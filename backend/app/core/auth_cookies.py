"""HttpOnly refresh cookie helpers and CSRF checks."""

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException, Request, Response, status

from app.config import get_settings

AuthClient = Literal["admin", "user"]
AUTH_CLIENTS: tuple[AuthClient, ...] = ("admin", "user")

REFRESH_COOKIE_ADMIN = "pg_refresh_admin"
REFRESH_COOKIE_USER = "pg_refresh_user"
REFRESH_COOKIE_NAMES = {
    "admin": REFRESH_COOKIE_ADMIN,
    "user": REFRESH_COOKIE_USER,
}


def cookie_name(client: AuthClient) -> str:
    return REFRESH_COOKIE_NAMES[client]


def get_refresh_cookie(request: Request, client: AuthClient) -> str | None:
    return request.cookies.get(cookie_name(client))


def set_refresh_cookie(response: Response, client: AuthClient, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=cookie_name(client),
        value=token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path=f"{settings.API_V1_PREFIX}/auth",
    )


def clear_refresh_cookie(response: Response, client: AuthClient) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=cookie_name(client),
        path=f"{settings.API_V1_PREFIX}/auth",
        secure=not settings.DEBUG,
        samesite="lax",
    )


def assert_refresh_csrf(request: Request) -> None:
    """Базовая CSRF-защита для refresh/logout: только same-origin XHR."""
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request")

    origin = request.headers.get("origin")
    if not origin:
        return

    settings = get_settings()
    if origin not in settings.cors_origins_list:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid origin")

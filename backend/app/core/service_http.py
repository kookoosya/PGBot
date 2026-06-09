"""Helpers for mapping service-layer errors to FastAPI HTTP responses."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import TypeVar

from fastapi import HTTPException

from app.services.service_errors import ServiceError

T = TypeVar("T")


def raise_http_for_service_error(exc: BaseException) -> None:
    """Translate a service error (``detail`` + ``status_code``) to ``HTTPException``."""
    status_code = int(getattr(exc, "status_code", 400))
    detail = str(getattr(exc, "detail", exc))
    raise HTTPException(status_code=status_code, detail=detail) from exc


def raise_http_for_service_errors(exc: BaseException, *error_types: type[ServiceError]) -> None:
    """Raise HTTP for matching service errors; re-raise anything else."""
    if isinstance(exc, error_types):
        raise_http_for_service_error(exc)
    raise exc


async def run_service_call(coro: Awaitable[T], *error_types: type[ServiceError]) -> T:
    """Await a service call and translate known ``ServiceError`` subclasses to HTTP."""
    try:
        return await coro
    except error_types as exc:
        raise_http_for_service_error(exc)

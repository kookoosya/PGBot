"""Helpers for mapping service-layer errors to FastAPI HTTP responses."""

from __future__ import annotations

from fastapi import HTTPException

from app.services.service_errors import ServiceError


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

"""Shared conventions for service-layer domain errors."""

from __future__ import annotations


class ServiceError(Exception):
    """Base service-layer exception with HTTP mapping hints."""

    detail: str
    status_code: int

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code

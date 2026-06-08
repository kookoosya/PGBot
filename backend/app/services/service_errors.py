"""Shared conventions for service-layer domain errors.

Every service exception exposes ``detail`` (human-readable message) and
``status_code`` (HTTP mapping hint) so API routers can translate them
uniformly via ``raise_http_for_service_error``.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Base class for recoverable business errors raised by service modules."""

    detail: str
    status_code: int

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code

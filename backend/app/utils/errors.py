"""Base service-layer exception used across domain services.

Subclasses should set ``status_code`` for HTTP mapping via ``raise_http_for_service_error``.
"""

from __future__ import annotations


class ServiceError(Exception):
    """Recoverable business error raised by service modules."""

    detail: str
    status_code: int

    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code

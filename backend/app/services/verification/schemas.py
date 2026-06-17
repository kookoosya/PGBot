"""Verification service errors."""

from app.utils.errors import ServiceError


class VerificationNotFoundError(ServiceError):
    def __init__(self, detail: str = "Пользователь не найден") -> None:
        super().__init__(detail, status_code=404)


class VerificationValidationError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)

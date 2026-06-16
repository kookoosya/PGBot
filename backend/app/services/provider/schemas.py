"""Provider domain errors."""

from app.utils.errors import ServiceError


class ProviderNotFoundError(ServiceError):
    def __init__(self, detail: str = "Мастер не найден") -> None:
        super().__init__(detail, status_code=404)


class ProviderValidationError(ServiceError):
    def __init__(self, detail: str, *, status_code: int = 400) -> None:
        super().__init__(detail, status_code=status_code)


class ProviderAccessDeniedError(ServiceError):
    def __init__(self, detail: str = "Доступ только для мастеров") -> None:
        super().__init__(detail, status_code=403)

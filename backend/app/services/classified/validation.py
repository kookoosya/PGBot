"""Classified ad submission validation and antifraud checks."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.classified.schemas import ClassifiedCreateInput, ClassifiedValidationError
from app.services.classified_antifraud import (
    check_phone_rate_limit,
    check_recent_duplicate,
    find_scam_phrase,
    validate_phone,
)
from app.services.ip_abuse import contains_suspicious_link


async def validate_create_input(db: AsyncSession, data: ClassifiedCreateInput) -> None:
    """Run all submission validations; raise ``ClassifiedValidationError`` on failure."""
    if data.website_url:
        raise ClassifiedValidationError("Не удалось отправить форму. Обновите страницу.")

    if not data.agree_rules:
        raise ClassifiedValidationError(
            "Подтвердите, что объявление честное и без предоплаты незнакомцам",
        )

    phone_err = validate_phone(data.phone)
    if phone_err:
        raise ClassifiedValidationError(phone_err)

    if find_scam_phrase(f"{data.title} {data.description}"):
        raise ClassifiedValidationError(
            "Текст похож на мошенническую схему. Уберите требование предоплаты или перевода.",
        )

    rate_err = await check_phone_rate_limit(db, data.phone)
    if rate_err:
        raise ClassifiedValidationError(rate_err, status_code=429)

    dup_err = await check_recent_duplicate(db, data.phone, data.title)
    if dup_err:
        raise ClassifiedValidationError(dup_err)

    if contains_suspicious_link(data.contact_telegram, data.contact_vk, data.address):
        raise ClassifiedValidationError("Ссылки в контактах не допускаются — укажите телефон.")

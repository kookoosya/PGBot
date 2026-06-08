"""Проверки объявлений: лимиты, телефон, типовые схемы обмана."""

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classified import ClassifiedAd
from app.models.enums import ClassifiedPaymentStatus

SCAM_KEYWORDS = (
    "предоплат",
    "аванс",
    "переведите",
    "перевод на карту",
    "залог",
    "комиссия",
    "обработка заявки",
    "telegram only",
    "только телеграм",
    "whatsapp only",
    "крипт",
    "bitcoin",
    "nft",
    "заработок без",
    "пассивный доход",
    "mlm",
    "пирамид",
)

PHONE_DIGITS_RE = re.compile(r"\D+")


def normalize_phone(phone: str) -> str:
    digits = PHONE_DIGITS_RE.sub("", phone or "")
    if len(digits) == 11 and digits.startswith("8"):
        digits = "7" + digits[1:]
    if len(digits) == 10:
        digits = "7" + digits
    return digits


def validate_phone(phone: str) -> str | None:
    digits = normalize_phone(phone)
    if len(digits) != 11 or not digits.startswith("7"):
        return "Укажите российский номер: +7 и 10 цифр"
    if digits[1] not in "389":
        return "Номер телефона выглядит некорректно"
    return None


def find_scam_phrase(text: str) -> str | None:
    low = (text or "").lower()
    for phrase in SCAM_KEYWORDS:
        if phrase in low:
            return phrase
    return None


async def check_phone_rate_limit(
    db: AsyncSession,
    phone: str,
    *,
    max_per_day: int = 3,
) -> str | None:
    digits = normalize_phone(phone)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    q = select(func.count(ClassifiedAd.id)).where(
        ClassifiedAd.created_at >= since,
        ClassifiedAd.payment_status.in_([
            ClassifiedPaymentStatus.PENDING,
            ClassifiedPaymentStatus.APPROVED,
        ]),
        or_(
            ClassifiedAd.phone == phone,
            ClassifiedAd.phone.like(f"%{digits[-10:]}%"),
        ),
    )
    count = (await db.execute(q)).scalar() or 0
    if count >= max_per_day:
        return f"С этого номера уже подано {count} объявлений за сутки. Попробуйте завтра."
    return None


async def check_recent_duplicate(
    db: AsyncSession,
    phone: str,
    title: str,
) -> str | None:
    digits = normalize_phone(phone)
    since = datetime.now(timezone.utc) - timedelta(days=7)
    title_key = re.sub(r"\s+", " ", (title or "").strip().lower())
    if len(title_key) < 5:
        return None
    result = await db.execute(
        select(ClassifiedAd.title)
        .where(
            ClassifiedAd.created_at >= since,
            ClassifiedAd.payment_status.in_([
                ClassifiedPaymentStatus.PENDING,
                ClassifiedPaymentStatus.APPROVED,
            ]),
            or_(
                ClassifiedAd.phone == phone,
                ClassifiedAd.phone.like(f"%{digits[-10:]}%"),
            ),
        )
        .limit(20)
    )
    for (existing_title,) in result.all():
        existing_key = re.sub(r"\s+", " ", (existing_title or "").strip().lower())
        if existing_key == title_key:
            return "Похожее объявление с этого номера уже на модерации или опубликовано."
    return None

"""Проверки объявлений: лимиты, телефон, типовые схемы обмана, качество текста."""

import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classified import ClassifiedAd
from app.models.enums import ClassifiedPaymentStatus
from app.services.vk.moderation import detect_profanity, detect_spam

MIN_TITLE_LEN = 5
MIN_DESC_LEN = 15
_REPEAT_CHAR_RE = re.compile(r"(.)\1{5,}")

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


def evaluate_classified_content(title: str, description: str) -> str | None:
    """Автопроверка текста объявления. None — можно публиковать."""
    title_clean = (title or "").strip()
    desc_clean = (description or "").strip()
    combined = f"{title_clean} {desc_clean}"

    if len(title_clean) < MIN_TITLE_LEN:
        return "Заголовок слишком короткий — опишите суть в нескольких словах."
    if len(desc_clean) < MIN_DESC_LEN:
        return "Описание слишком короткое — добавьте детали для соседей."
    if _REPEAT_CHAR_RE.search(title_clean) or _REPEAT_CHAR_RE.search(desc_clean):
        return "Текст выглядит как спам — уберите повторяющиеся символы."
    if detect_profanity(combined):
        return "Текст содержит недопустимые выражения. Переформулируйте объявление."
    if detect_spam(combined):
        return "Текст похож на спам (много ссылок или КАПС). Пишите обычным языком."
    letters = [c for c in title_clean if c.isalpha()]
    if letters and sum(1 for c in letters if c.isupper()) / len(letters) >= 0.85:
        return "Заголовок не должен быть полностью ЗАГЛАВНЫМИ — напишите обычным регистром."
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
            return "Похожее объявление с этого номера уже опубликовано."
    return None

"""Watch bank notification inbox and auto-activate AI Pro."""

from __future__ import annotations

import email
import imaplib
import logging
import re
from email.header import decode_header

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_payment_order import AIPaymentOrder
from app.models.bank_inbox_message import BankInboxMessage
from app.services.ai_bank_payment_service import bank_auto_enabled, fulfill_bank_order

logger = logging.getLogger(__name__)
settings = get_settings()

CODE_RE = re.compile(r"\bPG(\d{4,8})\b", re.IGNORECASE)


def _decode_header_value(value: str | None) -> str:
    if not value:
        return ""
    parts = decode_header(value)
    chunks: list[str] = []
    for chunk, encoding in parts:
        if isinstance(chunk, bytes):
            chunks.append(chunk.decode(encoding or "utf-8", errors="replace"))
        else:
            chunks.append(chunk)
    return " ".join(chunks)


def _extract_text(msg: email.message.Message) -> str:
    chunks: list[str] = []
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() not in {"text/plain", "text/html"}:
                continue
            payload = part.get_payload(decode=True)
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            chunks.append(payload.decode(charset, errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            chunks.append(payload.decode(charset, errors="replace"))
    return "\n".join(chunks)


def _fetch_unseen_messages() -> list[tuple[str, str]]:
    if not bank_auto_enabled():
        return []

    host = settings.BANK_IMAP_HOST.strip()
    user = settings.BANK_IMAP_USER.strip()
    password = settings.BANK_IMAP_PASSWORD
    folder = settings.BANK_IMAP_FOLDER.strip() or "INBOX"

    messages: list[tuple[str, str]] = []
    mail = imaplib.IMAP4_SSL(host)
    try:
        mail.login(user, password)
        mail.select(folder)
        status, data = mail.search(None, "UNSEEN")
        if status != "OK" or not data or not data[0]:
            return []

        for num in data[0].split():
            status, msg_data = mail.fetch(num, "(RFC822 UID)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            uid_match = re.search(r"UID (\d+)", msg_data[0][0].decode(errors="replace"))
            uid = uid_match.group(1) if uid_match else num.decode()
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject = _decode_header_value(msg.get("Subject"))
            body = _extract_text(msg)
            messages.append((f"{folder}:{uid}", f"{subject}\n{body}"))
    finally:
        try:
            mail.logout()
        except Exception:
            pass
    return messages


def _amount_matches(text: str, amount_rub: int) -> bool:
    patterns = [
        rf"\b{amount_rub}[,\.]?0{{0,2}}\s*(?:₽|руб|rub)\b",
        rf"(?:\+|зачислен|поступил|перевод).{{0,40}}\b{amount_rub}\b",
    ]
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


async def process_bank_inbox(db: AsyncSession) -> int:
    if not bank_auto_enabled():
        return 0

    activated = 0
    for message_uid, text in _fetch_unseen_messages():
        seen = await db.execute(
            select(BankInboxMessage).where(BankInboxMessage.message_uid == message_uid)
        )
        if seen.scalar_one_or_none():
            continue

        code_match = CODE_RE.search(text)
        if not code_match:
            db.add(BankInboxMessage(message_uid=message_uid))
            await db.flush()
            continue

        payment_code = f"PG{code_match.group(1)}"
        result = await db.execute(
            select(AIPaymentOrder).where(
                AIPaymentOrder.payment_code == payment_code,
                AIPaymentOrder.status == "pending",
            )
        )
        order = result.scalar_one_or_none()
        if order and _amount_matches(text, order.amount_rub):
            await fulfill_bank_order(db, order, reference=f"email:{message_uid}:{payment_code}")
            activated += 1
        elif order:
            logger.warning("Bank email matched code %s but amount not verified", payment_code)

        db.add(BankInboxMessage(message_uid=message_uid))
        await db.flush()

    return activated

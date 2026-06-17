"""Incoming complaint processing: AI analysis, deduplication and notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.ai_analysis import AIAnalysis
from app.models.department import Department
from app.models.enums import IssueStatus, NotificationPriority, NotificationStatus, Priority
from app.models.issue import Issue, IssuePhoto
from app.models.notification import Notification
from app.models.user import User
from app.schemas.analysis_result import AnalysisResult
from app.constants.portal_copy import ISSUE_ACCEPTED_VK, LINK_COMPLAINTS
from app.services.notifications import notify_owner, notify_vk_user_with_links
from app.services.telegram import notify_about_issue
from app.services.vk.client import send_message

from .dedup import handle_deduplication
from .category import normalize_issue_category
from .gemini_analysis import analyze_issue_with_context
from .residents import get_or_create_resident, get_or_create_web_resident

logger = logging.getLogger(__name__)
settings = get_settings()


async def find_department_by_name(db: AsyncSession, name: str) -> Department | None:
    """Match a department by partial name (case-insensitive)."""
    result = await db.execute(
        select(Department).where(Department.name.ilike(f"%{name}%"), Department.is_active.is_(True))
    )
    return result.scalar_one_or_none()


def _create_ai_analysis(
    issue_id: int,
    analysis: AnalysisResult,
    *,
    is_valid: bool,
    category: str | None = None,
    priority: str | None = None,
) -> AIAnalysis:
    return AIAnalysis(
        issue_id=issue_id,
        is_valid=is_valid,
        category=category if is_valid else analysis.category,
        priority=priority if is_valid else analysis.priority,
        summary=analysis.summary,
        duplicate_probability=analysis.duplicate_probability,
        suggested_department=analysis.suggested_department,
        raw_response=analysis.raw_response,
        model_version=settings.GEMINI_MODEL,
    )


async def _resolve_department(db: AsyncSession, analysis: AnalysisResult) -> Department | None:
    if analysis.suggested_department:
        return await find_department_by_name(db, analysis.suggested_department)
    return None


async def _create_issue_from_analysis(
    db: AsyncSession,
    text: str,
    analysis: AnalysisResult,
    resident: User,
    *,
    is_valid: bool,
    category: str | None = None,
    priority: str | None = None,
    address: str | None = None,
    department: Department | None = None,
    vk_message_id: int | None = None,
    vk_peer_id: int | None = None,
) -> Issue:
    if not is_valid:
        issue = Issue(
            description=text,
            status=IssueStatus.REJECTED,
            is_spam=True,
            resident_id=resident.id,
            address=address,
            vk_message_id=vk_message_id,
            vk_peer_id=vk_peer_id,
        )
    else:
        issue = Issue(
            title=analysis.summary_or(text[:100]),
            description=text,
            status=IssueStatus.NEW,
            category=normalize_issue_category(category),
            priority=priority or analysis.resolved_priority,
            address=address,
            resident_id=resident.id,
            department_id=department.id if department else None,
            vk_message_id=vk_message_id,
            vk_peer_id=vk_peer_id,
        )
    db.add(issue)
    await db.flush()
    return issue


def _notification_priority(priority: str) -> NotificationPriority:
    if priority in (Priority.HIGH.value, Priority.CRITICAL.value):
        return NotificationPriority.HIGH
    return NotificationPriority.NORMAL


async def _create_and_send_notification(
    db: AsyncSession,
    issue: Issue,
    analysis: AnalysisResult,
    text: str,
    *,
    category: str | None,
    priority: str,
    department: Department | None,
    owner_message: str,
) -> None:
    """Persist notification record and notify owner / Telegram for high priority."""
    summary = analysis.summary_or(text[:100])
    notif_priority = _notification_priority(priority)
    notification = Notification(
        issue_id=issue.id,
        channel="telegram",
        priority=notif_priority,
        message=f"Новое обращение #{issue.id}: {summary}",
    )
    db.add(notification)

    try:
        await notify_owner(owner_message)
    except Exception:
        logger.exception("Owner notification failed for issue #%s", issue.id)

    if notif_priority == NotificationPriority.HIGH:
        dept_chat = department.telegram_chat_id if department else None
        try:
            sent = await notify_about_issue(
                issue.id,
                summary,
                category,
                priority,
                issue.address,
                dept_chat,
                notif_priority,
            )
            if sent:
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now(timezone.utc)
        except Exception:
            logger.exception("Telegram notification failed for issue #%s", issue.id)


def _attach_vk_photos(db: AsyncSession, issue_id: int, photos: list[dict] | None) -> None:
    if not photos:
        return
    for photo in photos:
        db.add(IssuePhoto(issue_id=issue_id, url=photo["url"], vk_photo_id=photo.get("vk_photo_id")))


async def _persist_invalid_complaint(
    db: AsyncSession,
    text: str,
    analysis: AnalysisResult,
    resident: User,
    *,
    address: str | None = None,
    vk_message_id: int | None = None,
    vk_peer_id: int | None = None,
) -> Issue:
    issue = await _create_issue_from_analysis(
        db,
        text,
        analysis,
        resident,
        is_valid=False,
        address=address,
        vk_message_id=vk_message_id,
        vk_peer_id=vk_peer_id,
    )
    db.add(_create_ai_analysis(issue.id, analysis, is_valid=False))
    return issue


async def _persist_valid_complaint(
    db: AsyncSession,
    text: str,
    analysis: AnalysisResult,
    resident: User,
    *,
    category: str | None,
    address: str | None = None,
    vk_message_id: int | None = None,
    vk_peer_id: int | None = None,
    photos: list[dict] | None = None,
    owner_message: str,
) -> Issue:
    priority = analysis.resolved_priority
    department = await _resolve_department(db, analysis)
    issue = await _create_issue_from_analysis(
        db,
        text,
        analysis,
        resident,
        is_valid=True,
        category=category,
        priority=priority,
        address=address,
        department=department,
        vk_message_id=vk_message_id,
        vk_peer_id=vk_peer_id,
    )
    db.add(_create_ai_analysis(issue.id, analysis, is_valid=True, category=category, priority=priority))
    _attach_vk_photos(db, issue.id, photos)
    await _create_and_send_notification(
        db,
        issue,
        analysis,
        text,
        category=category,
        priority=priority,
        department=department,
        owner_message=owner_message.format(id=issue.id),
    )
    return issue


async def process_incoming_message(
    db: AsyncSession,
    text: str,
    vk_id: int,
    peer_id: int,
    message_id: int | None = None,
    photos: list[dict] | None = None,
) -> Issue | None:
    """Process a VK complaint: validate, analyze, deduplicate, persist and reply."""
    if not text or len(text.strip()) < 5:
        await send_message(
            peer_id,
            "Пожалуйста, опишите проблему подробнее (минимум 5 символов). "
            "Можно приложить фото.",
        )
        return None

    resident = await get_or_create_resident(db, vk_id)
    analysis, existing = await analyze_issue_with_context(db, text)

    if not analysis.is_valid:
        issue = await _persist_invalid_complaint(
            db,
            text,
            analysis,
            resident,
            vk_message_id=message_id,
            vk_peer_id=peer_id,
        )
        await send_message(
            peer_id,
            "Ваше сообщение не принято как обращение. "
            "Пожалуйста, опишите конкретную проблему в поселке без рекламы и оскорблений.",
        )
        return issue

    if parent_issue := await handle_deduplication(db, existing, analysis.duplicate_probability):
        await send_message(
            peer_id,
            f"Спасибо! Ваше обращение связано с существующей проблемой #{parent_issue.id}. "
            f"Подтверждений: {parent_issue.confirmation_count}",
        )
        return parent_issue

    category = analysis.category
    issue = await _persist_valid_complaint(
        db,
        text,
        analysis,
        resident,
        category=category,
        vk_message_id=message_id,
        vk_peer_id=peer_id,
        photos=photos,
        owner_message=(
            f"📋 Новое обращение #{{id}}\n"
            f"{analysis.summary_or(text[:120])}\n"
            f"Категория: {category or '—'}\n"
            f"От: VK id{vk_id}"
        ),
    )

    await notify_vk_user_with_links(
        peer_id,
        ISSUE_ACCEPTED_VK.format(
            id=issue.id,
            summary=analysis.summary_or(""),
            category=category or "—",
        ),
        (LINK_COMPLAINTS, f"/complaints?issue={issue.id}"),
    )
    return issue


async def process_web_complaint(
    db: AsyncSession,
    text: str,
    *,
    user: User | None = None,
    phone: str | None = None,
    full_name: str | None = None,
    address: str | None = None,
    category: str | None = None,
) -> Issue:
    """Process a web-form complaint through AI analysis and persistence."""
    resident = await get_or_create_web_resident(
        db, user=user, phone=phone, full_name=full_name
    )
    analysis, existing = await analyze_issue_with_context(db, text, category)

    if not analysis.is_valid:
        return await _persist_invalid_complaint(
            db,
            text,
            analysis,
            resident,
            address=address,
        )

    if parent_issue := await handle_deduplication(db, existing, analysis.duplicate_probability):
        return parent_issue

    resolved_category = category or analysis.category
    return await _persist_valid_complaint(
        db,
        text,
        analysis,
        resident,
        category=resolved_category,
        address=address,
        owner_message=(
            f"📋 Новое обращение #{{id}} (сайт)\n"
            f"{analysis.summary_or(text[:120])}\n"
            f"Категория: {resolved_category or '—'}\n"
            f"От: {resident.full_name or resident.username}"
        ),
    )

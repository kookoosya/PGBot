import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.ai_analysis import AIAnalysis
from app.models.department import Department
from app.models.enums import IssueStatus, NotificationPriority, NotificationStatus, Priority, UserRole
from app.models.issue import Issue, IssueDuplicate, IssuePhoto
from app.models.notification import Notification
from app.models.user import Role, User
from app.schemas.analysis_result import AnalysisResult
from app.services.gemini import GeminiAnalysisError, request_gemini_analysis
from app.services.issue_utils import issue_display_summary
from app.services.notifications import notify_owner
from app.services.telegram import notify_about_issue
from app.services.vk import send_message

logger = logging.getLogger(__name__)
settings = get_settings()

_GEMINI_MAX_ATTEMPTS = 2
_GEMINI_RETRY_DELAY_SEC = 0.75
_GEMINI_FAILURE_SUMMARY = (
    "Не удалось проанализировать обращение автоматически. Попробуйте позже."
)


def _is_transient_gemini_error(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, ConnectionError, OSError)):
        return True
    return type(exc).__name__ in {
        "ServiceUnavailable",
        "DeadlineExceeded",
        "InternalServerError",
        "TooManyRequests",
        "ResourceExhausted",
        "GoogleAPIError",
        "RetryError",
    }


def _gemini_failure_result(exc: Exception) -> AnalysisResult:
    return AnalysisResult(
        is_valid=False,
        summary=_GEMINI_FAILURE_SUMMARY,
        raw_response={"error": str(exc)},
    )


async def _run_gemini_with_retry(text: str, context: str) -> AnalysisResult:
    """Call Gemini with one retry on transient failures."""
    last_exc: Exception | None = None
    for attempt in range(1, _GEMINI_MAX_ATTEMPTS + 1):
        try:
            raw = await request_gemini_analysis(text, context)
            return AnalysisResult.from_gemini(raw)
        except GeminiAnalysisError as exc:
            last_exc = exc
            if attempt < _GEMINI_MAX_ATTEMPTS and _is_transient_gemini_error(exc):
                logger.warning(
                    "Gemini analysis attempt %s/%s failed (%s), retrying",
                    attempt,
                    _GEMINI_MAX_ATTEMPTS,
                    exc,
                )
                await asyncio.sleep(_GEMINI_RETRY_DELAY_SEC * attempt)
                continue
            logger.warning("Gemini analysis failed after %s attempt(s): %s", attempt, exc)
            return _gemini_failure_result(exc)
        except Exception as exc:
            logger.warning("Unexpected error during Gemini analysis: %s", exc)
            return _gemini_failure_result(exc)
    return _gemini_failure_result(last_exc or GeminiAnalysisError("unknown"))


async def get_or_create_web_resident(
    db: AsyncSession,
    *,
    user: User | None = None,
    phone: str | None = None,
    full_name: str | None = None,
) -> User:
    if user:
        return user

    if phone:
        result = await db.execute(
            select(User).options(selectinload(User.role)).where(User.phone == phone)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    role = await _get_resident_role(db)
    suffix = phone or "web"
    return await _create_resident_user(
        db,
        username=f"web_{suffix.replace('+', '').replace(' ', '')}_{int(datetime.now(timezone.utc).timestamp())}",
        full_name=full_name or "Житель сайта",
        role_id=role.id,
        phone=phone,
    )


async def get_or_create_resident(db: AsyncSession, vk_id: int) -> User:
    result = await db.execute(
        select(User).options(selectinload(User.role)).where(User.vk_id == vk_id)
    )
    user = result.scalar_one_or_none()
    if user:
        return user

    role = await _get_resident_role(db)
    return await _create_resident_user(
        db,
        username=f"vk_{vk_id}",
        full_name=f"Житель VK {vk_id}",
        role_id=role.id,
        vk_id=vk_id,
    )


async def find_similar_issues(db: AsyncSession, text: str, category: str | None) -> list[Issue]:
    query = (
        select(Issue)
        .options(selectinload(Issue.ai_analysis))
        .where(
            Issue.is_spam.is_(False),
            Issue.status.notin_([IssueStatus.RESOLVED, IssueStatus.REJECTED, IssueStatus.ARCHIVED]),
            Issue.parent_issue_id.is_(None),
        )
        .order_by(Issue.created_at.desc())
        .limit(20)
    )
    if category:
        query = query.where(Issue.category == category)

    result = await db.execute(query)
    return list(result.scalars().all())


async def find_department_by_name(db: AsyncSession, name: str) -> Department | None:
    result = await db.execute(
        select(Department).where(Department.name.ilike(f"%{name}%"), Department.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def _get_resident_role(db: AsyncSession) -> Role:
    result = await db.execute(select(Role).where(Role.name == UserRole.RESIDENT))
    return result.scalar_one()


async def _create_resident_user(
    db: AsyncSession,
    *,
    username: str,
    full_name: str,
    role_id: int,
    phone: str | None = None,
    vk_id: int | None = None,
) -> User:
    user = User(
        username=username,
        phone=phone,
        vk_id=vk_id,
        full_name=full_name,
        role_id=role_id,
    )
    db.add(user)
    await db.flush()
    return user


async def _analyze_issue_with_context(
    db: AsyncSession,
    text: str,
    category: str | None = None,
) -> tuple[AnalysisResult, list[Issue]]:
    """Find similar issues, build context and run Gemini analysis."""
    existing = await find_similar_issues(db, text, category)
    context_lines = [
        f"#{issue.id}: {issue_display_summary(issue)}"
        for issue in existing[:5]
    ]
    analysis = await _run_gemini_with_retry(text, "\n".join(context_lines))
    return analysis, existing


async def _handle_deduplication(
    db: AsyncSession,
    existing: list[Issue],
    duplicate_prob: float,
) -> Issue | None:
    """Link complaint to an existing issue when duplicate probability is high."""
    if duplicate_prob >= settings.DUPLICATE_THRESHOLD and existing:
        parent_issue = existing[0]
        parent_issue.confirmation_count += 1
        db.add(
            IssueDuplicate(
                issue_id=parent_issue.id,
                duplicate_of_id=parent_issue.id,
                similarity_score=duplicate_prob,
            )
        )
        return parent_issue
    return None


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
            category=category,
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
    await notify_owner(owner_message)

    if notif_priority == NotificationPriority.HIGH:
        dept_chat = department.telegram_chat_id if department else None
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
    if not text or len(text.strip()) < 5:
        await send_message(
            peer_id,
            "Пожалуйста, опишите проблему подробнее (минимум 5 символов). "
            "Можно приложить фото.",
        )
        return None

    resident = await get_or_create_resident(db, vk_id)
    analysis, existing = await _analyze_issue_with_context(db, text)

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

    if parent_issue := await _handle_deduplication(db, existing, analysis.duplicate_probability):
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

    await send_message(
        peer_id,
        f"✅ Обращение #{issue.id} принято!\n"
        f"📋 {analysis.summary_or('')}\n"
        f"📁 Категория: {category}\n"
        f"Статус: на рассмотрении",
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
    resident = await get_or_create_web_resident(
        db, user=user, phone=phone, full_name=full_name
    )
    analysis, existing = await _analyze_issue_with_context(db, text, category)

    if not analysis.is_valid:
        return await _persist_invalid_complaint(
            db,
            text,
            analysis,
            resident,
            address=address,
        )

    if parent_issue := await _handle_deduplication(db, existing, analysis.duplicate_probability):
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

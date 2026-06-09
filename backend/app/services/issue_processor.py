import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.ai_analysis import AIAnalysis
from app.models.department import Department
from app.models.enums import (
    IssueStatus,
    NotificationPriority,
    NotificationStatus,
    Priority,
    UserRole,
)
from app.models.issue import Issue, IssueDuplicate, IssuePhoto
from app.models.notification import Notification
from app.models.user import User
from app.services.gemini import analyze_issue
from app.services.issue.validation import find_similar_issues
from app.services.notifications import notify_owner
from app.services.telegram import notify_about_issue
from app.services.vk import send_message

logger = logging.getLogger(__name__)
settings = get_settings()


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
        result = await db.execute(select(User).options(selectinload(User.role)).where(User.phone == phone))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    from app.models.user import Role

    role_result = await db.execute(select(Role).where(Role.name == UserRole.RESIDENT))
    role = role_result.scalar_one()
    suffix = phone or "web"
    user = User(
        username=f"web_{suffix.replace('+', '').replace(' ', '')}_{int(datetime.now(UTC).timestamp())}",
        phone=phone,
        full_name=full_name or "Житель сайта",
        role_id=role.id,
    )
    db.add(user)
    await db.flush()
    return user


async def get_or_create_resident(db: AsyncSession, vk_id: int) -> User:
    result = await db.execute(select(User).options(selectinload(User.role)).where(User.vk_id == vk_id))
    user = result.scalar_one_or_none()
    if user:
        return user

    from app.models.user import Role

    role_result = await db.execute(select(Role).where(Role.name == UserRole.RESIDENT))
    role = role_result.scalar_one()
    user = User(
        username=f"vk_{vk_id}",
        vk_id=vk_id,
        full_name=f"Житель VK {vk_id}",
        role_id=role.id,
    )
    db.add(user)
    await db.flush()
    return user




async def find_department_by_name(db: AsyncSession, name: str) -> Department | None:
    result = await db.execute(
        select(Department).where(Department.name.ilike(f"%{name}%"), Department.is_active.is_(True))
    )
    return result.scalar_one_or_none()


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
            "Пожалуйста, опишите проблему подробнее (минимум 5 символов). " "Можно приложить фото.",
        )
        return None

    resident = await get_or_create_resident(db, vk_id)

    existing = await find_similar_issues(db, text, None)
    context_lines = []
    for issue in existing[:5]:
        summary = issue.ai_analysis.summary if issue.ai_analysis else issue.description[:100]
        context_lines.append(f"#{issue.id}: {summary}")

    analysis = await analyze_issue(text, "\n".join(context_lines))

    if not analysis.get("is_valid", True):
        issue = Issue(
            description=text,
            status=IssueStatus.REJECTED,
            is_spam=True,
            resident_id=resident.id,
            vk_message_id=message_id,
            vk_peer_id=peer_id,
        )
        db.add(issue)
        await db.flush()

        ai = AIAnalysis(
            issue_id=issue.id,
            is_valid=False,
            category=analysis.get("category"),
            priority=analysis.get("priority"),
            summary=analysis.get("summary"),
            duplicate_probability=analysis.get("duplicate_probability"),
            suggested_department=analysis.get("suggested_department"),
            raw_response=analysis,
            model_version=settings.GEMINI_MODEL,
        )
        db.add(ai)
        await send_message(
            peer_id,
            "Ваше сообщение не принято как обращение. "
            "Пожалуйста, опишите конкретную проблему в поселке без рекламы и оскорблений.",
        )
        return issue

    duplicate_prob = analysis.get("duplicate_probability", 0.0)
    parent_issue = None

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
        await send_message(
            peer_id,
            f"Спасибо! Ваше обращение связано с существующей проблемой #{parent_issue.id}. "
            f"Подтверждений: {parent_issue.confirmation_count}",
        )
        return parent_issue

    category = analysis.get("category")
    priority = analysis.get("priority", Priority.MEDIUM.value)
    department = None
    if suggested := analysis.get("suggested_department"):
        department = await find_department_by_name(db, suggested)

    issue = Issue(
        title=analysis.get("summary", text[:100]),
        description=text,
        status=IssueStatus.NEW,
        category=category,
        priority=priority,
        resident_id=resident.id,
        department_id=department.id if department else None,
        vk_message_id=message_id,
        vk_peer_id=peer_id,
    )
    db.add(issue)
    await db.flush()

    ai = AIAnalysis(
        issue_id=issue.id,
        is_valid=True,
        category=category,
        priority=priority,
        summary=analysis.get("summary"),
        duplicate_probability=duplicate_prob,
        suggested_department=analysis.get("suggested_department"),
        raw_response=analysis,
        model_version=settings.GEMINI_MODEL,
    )
    db.add(ai)

    if photos:
        for photo in photos:
            db.add(IssuePhoto(issue_id=issue.id, url=photo["url"], vk_photo_id=photo.get("vk_photo_id")))

    notif_priority = (
        NotificationPriority.HIGH
        if priority in (Priority.HIGH.value, Priority.CRITICAL.value)
        else NotificationPriority.NORMAL
    )
    notification = Notification(
        issue_id=issue.id,
        channel="telegram",
        priority=notif_priority,
        message=f"Новое обращение #{issue.id}: {analysis.get('summary', text[:100])}",
    )
    db.add(notification)

    await notify_owner(
        f"📋 Новое обращение #{issue.id}\n"
        f"{analysis.get('summary', text[:120])}\n"
        f"Категория: {category or '—'}\n"
        f"От: VK id{vk_id}"
    )

    if notif_priority == NotificationPriority.HIGH:
        dept_chat = department.telegram_chat_id if department else None
        sent = await notify_about_issue(
            issue.id,
            analysis.get("summary", text[:100]),
            category,
            priority,
            issue.address,
            dept_chat,
            notif_priority,
        )
        if sent:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(UTC)

    await send_message(
        peer_id,
        f"✅ Обращение #{issue.id} принято!\n"
        f"📋 {analysis.get('summary', '')}\n"
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
    resident = await get_or_create_web_resident(db, user=user, phone=phone, full_name=full_name)

    existing = await find_similar_issues(db, text, category)
    context_lines = []
    for issue in existing[:5]:
        summary = issue.ai_analysis.summary if issue.ai_analysis else issue.description[:100]
        context_lines.append(f"#{issue.id}: {summary}")

    analysis = await analyze_issue(text, "\n".join(context_lines))

    if not analysis.get("is_valid", True):
        issue = Issue(
            description=text,
            status=IssueStatus.REJECTED,
            is_spam=True,
            resident_id=resident.id,
            address=address,
        )
        db.add(issue)
        await db.flush()
        ai = AIAnalysis(
            issue_id=issue.id,
            is_valid=False,
            category=analysis.get("category"),
            priority=analysis.get("priority"),
            summary=analysis.get("summary"),
            duplicate_probability=analysis.get("duplicate_probability"),
            suggested_department=analysis.get("suggested_department"),
            raw_response=analysis,
            model_version=settings.GEMINI_MODEL,
        )
        db.add(ai)
        return issue

    duplicate_prob = analysis.get("duplicate_probability", 0.0)
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

    resolved_category = category or analysis.get("category")
    priority = analysis.get("priority", Priority.MEDIUM.value)
    department = None
    if suggested := analysis.get("suggested_department"):
        department = await find_department_by_name(db, suggested)

    issue = Issue(
        title=analysis.get("summary", text[:100]),
        description=text,
        status=IssueStatus.NEW,
        category=resolved_category,
        priority=priority,
        address=address,
        resident_id=resident.id,
        department_id=department.id if department else None,
    )
    db.add(issue)
    await db.flush()

    ai = AIAnalysis(
        issue_id=issue.id,
        is_valid=True,
        category=resolved_category,
        priority=priority,
        summary=analysis.get("summary"),
        duplicate_probability=duplicate_prob,
        suggested_department=analysis.get("suggested_department"),
        raw_response=analysis,
        model_version=settings.GEMINI_MODEL,
    )
    db.add(ai)

    notif_priority = (
        NotificationPriority.HIGH
        if priority in (Priority.HIGH.value, Priority.CRITICAL.value)
        else NotificationPriority.NORMAL
    )
    notification = Notification(
        issue_id=issue.id,
        channel="telegram",
        priority=notif_priority,
        message=f"Новое обращение #{issue.id}: {analysis.get('summary', text[:100])}",
    )
    db.add(notification)

    await notify_owner(
        f"📋 Новое обращение #{issue.id} (сайт)\n"
        f"{analysis.get('summary', text[:120])}\n"
        f"Категория: {resolved_category or '—'}\n"
        f"От: {resident.full_name or resident.username}"
    )

    if notif_priority == NotificationPriority.HIGH:
        dept_chat = department.telegram_chat_id if department else None
        sent = await notify_about_issue(
            issue.id,
            analysis.get("summary", text[:100]),
            resolved_category,
            priority,
            issue.address,
            dept_chat,
            notif_priority,
        )
        if sent:
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.now(UTC)

    return issue

"""Audit logging and VK status notifications for issues."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.services.audit import log_action
from app.services.notifications import notify_issue_status

from .schemas import IssueActorContext

logger = logging.getLogger(__name__)


def status_value(status: IssueStatus | str) -> str:
    """Return enum value as string for logging and audit payloads."""
    return status.value if isinstance(status, IssueStatus) else str(status)


async def safe_audit(
    db: AsyncSession,
    action: str,
    issue_id: int,
    actor: IssueActorContext,
    details: dict[str, Any],
) -> bool:
    """Write audit log; return ``True`` on success."""
    try:
        await log_action(
            db,
            action,
            "issue",
            issue_id,
            user_id=actor.actor_id,
            details=details,
            ip_address=actor.ip_address,
        )
        return True
    except Exception:
        logger.exception(
            "Audit log failed for issue #%s: action=%s actor_id=%s ip=%s",
            issue_id,
            action,
            actor.actor_id,
            actor.ip_address,
        )
        return False


async def safe_notify_status(issue: Issue, *, previous_status: str | None = None) -> bool:
    """Notify resident in VK about status change; return ``True`` when delivered."""
    peer_id = getattr(issue, "vk_peer_id", None)
    if not peer_id:
        logger.info(
            "Status notification skipped for issue #%s — no vk_peer_id (web-only resident)",
            issue.id,
        )
        return False
    try:
        return await notify_issue_status(issue, previous_status=previous_status)
    except Exception:
        logger.exception(
            "VK status notification failed for issue #%s (status=%s peer_id=%s)",
            issue.id,
            status_value(issue.status),
            peer_id,
        )
        return False

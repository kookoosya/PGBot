"""Audit logging and resident notifications for issue lifecycle."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.issue import Issue
from app.services.audit import log_action
from app.services.issue.schemas import IssueActorContext
from app.services.notifications import notify_issue_status

logger = logging.getLogger(__name__)


async def safe_issue_audit(
    db: AsyncSession,
    action: str,
    issue_id: int,
    actor: IssueActorContext,
    details: dict[str, Any],
) -> bool:
    """Write audit log for an issue action; return ``True`` on success."""
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
            "Audit log failed for issue #%s: action=%s actor_id=%s",
            issue_id,
            action,
            actor.actor_id,
        )
        return False


async def safe_notify_status(issue: Issue) -> bool:
    """Notify resident in VK about status change; return ``True`` on success."""
    try:
        await notify_issue_status(issue)
        return True
    except Exception:
        logger.exception(
            "Status notification failed for issue #%s (status=%s peer_id=%s)",
            issue.id,
            issue.status,
            getattr(issue, "vk_peer_id", None),
        )
        return False

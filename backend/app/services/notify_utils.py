"""Safe notification helpers shared across service modules."""

from __future__ import annotations

import logging

from app.services.notifications import notify_owner

logger = logging.getLogger(__name__)


async def safe_notify_owner(
    message: str,
    *,
    context: str,
    resource: str,
    resource_id: int,
) -> bool:
    """Send a notification to the site owner; return ``True`` on success."""
    try:
        await notify_owner(message)
        return True
    except Exception:
        logger.exception(
            "Owner notification failed for %s #%s during %s",
            resource,
            resource_id,
            context,
        )
        return False

"""Safe notification wrappers that never raise to callers."""

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
    """Notify site owner; return ``True`` on success, log and return ``False`` on failure."""
    try:
        await notify_owner(message)
        return True
    except Exception:
        logger.exception(
            "Owner notification failed (%s): resource=%s id=%s",
            context,
            resource,
            resource_id,
        )
        return False

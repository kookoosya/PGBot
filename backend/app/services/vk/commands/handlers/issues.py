"""Resident issues commands."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.constants.portal_copy import LINK_COMPLAINTS
from app.models.issue import Issue
from app.services.issue_utils import issue_display_summary
from app.services.notifications import issue_status_hint
from app.services.vk.context import VkRouteContext
from app.services.vk.helpers import ISSUE_STATUS_EMOJI, send_with_site_links


async def handle_my_issues(ctx: VkRouteContext) -> None:
    result = await ctx.db.execute(
        select(Issue)
        .options(selectinload(Issue.ai_analysis))
        .where(Issue.vk_peer_id == ctx.peer_id, Issue.parent_issue_id.is_(None))
        .order_by(Issue.created_at.desc())
        .limit(10)
    )
    issues = result.scalars().all()
    if not issues:
        await send_with_site_links(
            ctx.peer_id,
            "📋 Обращений пока нет.\n\nОпишите проблему — примем заявку!",
            (LINK_COMPLAINTS, "/complaints"),
        )
        return

    lines = ["📋 Ваши обращения:\n"]
    for issue in issues:
        emoji = ISSUE_STATUS_EMOJI.get(issue.status, "📋")
        status_val = issue.status.value if hasattr(issue.status, "value") else str(issue.status)
        hint = issue_status_hint(status_val)
        lines.append(f"{emoji} #{issue.id} — {issue_display_summary(issue, max_len=50)}")
        if hint:
            lines.append(f"   {hint}")
    latest = issues[0]
    await send_with_site_links(
        ctx.peer_id,
        "\n".join(lines),
        (LINK_COMPLAINTS, f"/complaints?issue={latest.id}"),
    )

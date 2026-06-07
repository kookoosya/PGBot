import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.database import get_db
from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.services.issue_processor import process_incoming_message
from app.services.vk import get_welcome_keyboard, parse_vk_message, send_message

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter()


@router.post("/callback")
async def vk_callback(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    body: dict[str, Any] = await request.json()
    event_type = body.get("type")

    if event_type == "confirmation":
        return PlainTextResponse(settings.VK_CONFIRMATION_CODE)

    if event_type == "message_new":
        if settings.VK_SECRET_KEY and body.get("secret") != settings.VK_SECRET_KEY:
            return PlainTextResponse("ok")

        parsed = parse_vk_message(body)
        if not parsed:
            return PlainTextResponse("ok")

        text = parsed["text"]
        from_id = parsed["from_id"]
        peer_id = parsed["peer_id"]

        if text.lower() in ("начать", "start", "привет", "здравствуйте"):
            await send_message(
                peer_id,
                "👋 Добро пожаловать в «Народный Контроль Пушкинские Горы»!\n\n"
                "Опишите проблему в поселке — мы примем ваше обращение и передадим "
                "ответственным службам.\n\n"
                "Можно приложить фото.",
                keyboard=get_welcome_keyboard(),
            )
            return PlainTextResponse("ok")

        if text.lower() in ("📋 мои обращения", "мои обращения"):
            result = await db.execute(
                select(Issue)
                .options(selectinload(Issue.ai_analysis))
                .where(Issue.vk_peer_id == peer_id, Issue.parent_issue_id.is_(None))
                .order_by(Issue.created_at.desc())
                .limit(10)
            )
            issues = result.scalars().all()
            if not issues:
                await send_message(peer_id, "У вас пока нет обращений.")
            else:
                lines = ["📋 Ваши обращения:\n"]
                status_emoji = {
                    IssueStatus.NEW: "🆕",
                    IssueStatus.UNDER_REVIEW: "🔍",
                    IssueStatus.ASSIGNED: "👤",
                    IssueStatus.IN_PROGRESS: "🔧",
                    IssueStatus.RESOLVED: "✅",
                    IssueStatus.REJECTED: "❌",
                    IssueStatus.ARCHIVED: "📦",
                }
                for issue in issues:
                    emoji = status_emoji.get(issue.status, "📋")
                    summary = issue.ai_analysis.summary if issue.ai_analysis else issue.description[:50]
                    lines.append(f"{emoji} #{issue.id} — {summary} ({issue.status.value})")
                await send_message(peer_id, "\n".join(lines))
            return PlainTextResponse("ok")

        if text.lower() in ("ℹ️ как отправить обращение", "как отправить обращение", "помощь"):
            await send_message(
                peer_id,
                "ℹ️ Как отправить обращение:\n\n"
                "1. Опишите проблему текстом\n"
                "2. Укажите адрес или ориентир\n"
                "3. Приложите фото (по желанию)\n\n"
                "Пример: «Не работает фонарь на ул. Ленина, 15»",
            )
            return PlainTextResponse("ok")

        try:
            await process_incoming_message(
                db,
                text=text,
                vk_id=from_id,
                peer_id=peer_id,
                message_id=parsed.get("message_id"),
                photos=parsed.get("photos"),
            )
        except Exception as e:
            logger.exception("Error processing VK message: %s", e)
            await send_message(
                peer_id,
                "Произошла ошибка при обработке обращения. Попробуйте позже.",
            )

    return PlainTextResponse("ok")

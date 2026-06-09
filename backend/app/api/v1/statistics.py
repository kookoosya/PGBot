from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.database import get_db
from app.models.user import User
from app.schemas.statistics import StatisticsResponse
from app.services.statistics_service import build_issue_statistics

router = APIRouter()


@router.get("", response_model=StatisticsResponse)
async def get_statistics(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    return await build_issue_statistics(db)

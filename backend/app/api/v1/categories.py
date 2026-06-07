from fastapi import APIRouter

from app.models.enums import IssueCategory

router = APIRouter()


@router.get("")
async def list_categories():
    return [{"value": c.name, "label": c.value} for c in IssueCategory]

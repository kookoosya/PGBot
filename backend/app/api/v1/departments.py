from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from app.services.department_service import (
    DepartmentNotFoundError,
    create_department,
    department_to_response,
    list_departments,
    update_department,
)

router = APIRouter()


@router.get("", response_model=list[DepartmentResponse])
async def list_departments_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    active_only: bool = True,
):
    departments = await list_departments(db, active_only=active_only)
    return [department_to_response(dept) for dept in departments]


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department_endpoint(
    data: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    dept = await create_department(db, data)
    return department_to_response(dept)


@router.patch("/{dept_id}", response_model=DepartmentResponse)
async def update_department_endpoint(
    dept_id: int,
    data: DepartmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    try:
        dept = await update_department(db, dept_id, data)
    except DepartmentNotFoundError as exc:
        raise_http_for_service_error(exc)
    return department_to_response(dept)

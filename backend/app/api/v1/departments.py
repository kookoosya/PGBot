from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_roles
from app.database import get_db
from app.models.department import Department
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate

router = APIRouter()


@router.get("", response_model=list[DepartmentResponse])
async def list_departments(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(
        UserRole.MODERATOR, UserRole.ADMINISTRATION, UserRole.SOCIAL_SERVICE, UserRole.SUPER_ADMIN
    ))],
    active_only: bool = True,
):
    query = select(Department)
    if active_only:
        query = query.where(Department.is_active.is_(True))
    result = await db.execute(query.order_by(Department.name))
    return [DepartmentResponse.model_validate(d) for d in result.scalars().all()]


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    data: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMINISTRATION))],
):
    dept = Department(**data.model_dump())
    db.add(dept)
    await db.flush()
    return DepartmentResponse.model_validate(dept)


@router.patch("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: int,
    data: DepartmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.ADMINISTRATION))],
):
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)

    return DepartmentResponse.model_validate(dept)

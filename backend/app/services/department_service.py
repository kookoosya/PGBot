"""Department CRUD for the admin panel.

Public API: ``list_departments``, ``create_department``, ``update_department``.
Errors: ``DepartmentNotFoundError``.
"""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from app.utils.errors import ServiceError

logger = logging.getLogger(__name__)


class DepartmentNotFoundError(ServiceError):
    def __init__(self, detail: str = "Department not found") -> None:
        super().__init__(detail, status_code=404)


def department_to_response(dept: Department) -> DepartmentResponse:
    """Map department ORM row to API response."""
    return DepartmentResponse.model_validate(dept)


async def list_departments(
    db: AsyncSession,
    *,
    active_only: bool = True,
) -> list[Department]:
    """Return departments ordered by name."""
    query = select(Department)
    if active_only:
        query = query.where(Department.is_active.is_(True))
    result = await db.execute(query.order_by(Department.name))
    return list(result.scalars().all())


async def create_department(db: AsyncSession, data: DepartmentCreate) -> Department:
    """Create a new department."""
    dept = Department(**data.model_dump())
    db.add(dept)
    await db.flush()
    return dept


async def update_department(
    db: AsyncSession,
    dept_id: int,
    data: DepartmentUpdate,
) -> Department:
    """Apply partial updates to a department."""
    result = await db.execute(select(Department).where(Department.id == dept_id))
    dept = result.scalar_one_or_none()
    if not dept:
        raise DepartmentNotFoundError()

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(dept, field, value)
    return dept

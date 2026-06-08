from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.database import get_db
from app.models.catalog_item import CatalogItem
from app.models.enums import CATALOG_CATEGORY_LABELS, CatalogCategory, CatalogSource
from app.models.user import User
from app.schemas.catalog import (
    CatalogItemAdminResponse,
    CatalogItemCreate,
    CatalogItemResponse,
    CatalogItemUpdate,
)

router = APIRouter()


def _item_response(item: CatalogItem, *, admin: bool = False) -> dict:
    base = {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "category_label": CATALOG_CATEGORY_LABELS.get(item.category, item.category),
        "description": item.description,
        "phone": item.phone,
        "external_url": item.external_url,
        "price_hint": item.price_hint,
        "address": item.address,
        "source": item.source,
        "is_internal": item.is_internal,
        "sort_order": item.sort_order,
    }
    if admin:
        base.update({
            "is_active": item.is_active,
            "seed_key": item.seed_key,
            "created_at": item.created_at,
        })
    return base


@router.get("/categories")
async def list_catalog_categories():
    return [
        {"value": c.value, "label": CATALOG_CATEGORY_LABELS[c]}
        for c in CatalogCategory
        if c not in (CatalogCategory.AVITO,)
    ]


@router.get("/items", response_model=list[CatalogItemResponse])
async def list_public_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: CatalogCategory | None = None,
):
    query = (
        select(CatalogItem)
        .where(
            CatalogItem.is_active.is_(True),
            CatalogItem.is_internal.is_(False),
            CatalogItem.source != CatalogSource.AVITO,
            CatalogItem.category != CatalogCategory.AVITO,
        )
        .order_by(CatalogItem.sort_order, CatalogItem.name)
    )
    if category:
        query = query.where(CatalogItem.category == category)
    result = await db.execute(query)
    return [_item_response(i) for i in result.scalars().all()]


@router.get("/admin/items", response_model=list[CatalogItemAdminResponse])
async def list_admin_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    internal_only: bool = Query(False),
):
    query = select(CatalogItem).order_by(
        CatalogItem.is_internal.desc(),
        CatalogItem.sort_order,
        CatalogItem.name,
    )
    if internal_only:
        query = query.where(CatalogItem.is_internal.is_(True))
    result = await db.execute(query)
    return [_item_response(i, admin=True) for i in result.scalars().all()]


@router.post("/admin/items", response_model=CatalogItemAdminResponse, status_code=201)
async def create_admin_item(
    data: CatalogItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    item = CatalogItem(
        name=data.name,
        category=data.category,
        description=data.description,
        phone=data.phone,
        external_url=data.external_url,
        price_hint=data.price_hint,
        address=data.address,
        source=CatalogSource.INTERNAL,
        is_internal=data.is_internal,
        is_active=True,
        sort_order=data.sort_order,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return _item_response(item, admin=True)


@router.patch("/admin/items/{item_id}", response_model=CatalogItemAdminResponse)
async def update_admin_item(
    item_id: int,
    data: CatalogItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await db.execute(select(CatalogItem).where(CatalogItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Запись не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return _item_response(item, admin=True)


@router.delete("/admin/items/{item_id}", status_code=204)
async def delete_admin_item(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await db.execute(select(CatalogItem).where(CatalogItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(404, "Запись не найдена")
    if item.seed_key:
        item.is_active = False
    else:
        await db.delete(item)

"""Catalog items — public list and admin CRUD.

Public API: ``search_public_items``, ``list_admin_items``, ``create_catalog_item``,
``update_catalog_item``, ``delete_catalog_item``, ``catalog_item_to_response``.
Errors: ``CatalogNotFoundError``.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog_item import CatalogItem
from app.models.enums import CATALOG_CATEGORY_LABELS, CatalogCategory, CatalogSource
from app.schemas.catalog import CatalogItemCreate, CatalogItemUpdate
from app.utils.errors import ServiceError

logger = logging.getLogger(__name__)


class CatalogNotFoundError(ServiceError):
    def __init__(self, detail: str = "Запись не найдена") -> None:
        super().__init__(detail, status_code=404)


def list_catalog_category_options() -> list[dict[str, str]]:
    """Return category enum options excluding Avito."""
    return [
        {"value": category.value, "label": CATALOG_CATEGORY_LABELS[category]}
        for category in CatalogCategory
        if category not in (CatalogCategory.AVITO,)
    ]


def catalog_item_to_response(item: CatalogItem, *, admin: bool = False) -> dict:
    """Map catalog item ORM row to API payload."""
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


async def search_public_items(
    db: AsyncSession,
    *,
    category: Optional[CatalogCategory] = None,
) -> list[CatalogItem]:
    """Return active public catalog items."""
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
    return list(result.scalars().all())


async def list_admin_items(
    db: AsyncSession,
    *,
    internal_only: bool = False,
) -> list[CatalogItem]:
    """Return catalog items for admin management."""
    query = select(CatalogItem).order_by(
        CatalogItem.is_internal.desc(),
        CatalogItem.sort_order,
        CatalogItem.name,
    )
    if internal_only:
        query = query.where(CatalogItem.is_internal.is_(True))
    result = await db.execute(query)
    return list(result.scalars().all())


async def create_catalog_item(db: AsyncSession, data: CatalogItemCreate) -> CatalogItem:
    """Create a new catalog item."""
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
    return item


async def update_catalog_item(
    db: AsyncSession,
    item_id: int,
    data: CatalogItemUpdate,
) -> CatalogItem:
    """Apply partial updates to a catalog item."""
    result = await db.execute(select(CatalogItem).where(CatalogItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise CatalogNotFoundError()

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


async def delete_catalog_item(db: AsyncSession, item_id: int) -> None:
    """Soft-delete seeded items or hard-delete manual entries."""
    result = await db.execute(select(CatalogItem).where(CatalogItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise CatalogNotFoundError()
    if item.seed_key:
        item.is_active = False
    else:
        await db.delete(item)

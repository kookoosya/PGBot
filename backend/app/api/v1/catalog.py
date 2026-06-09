from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import require_owner
from app.core.service_http import raise_http_for_service_error
from app.database import get_db
from app.models.enums import CatalogCategory
from app.models.user import User
from app.schemas.catalog import (
    CatalogItemAdminResponse,
    CatalogItemCreate,
    CatalogItemResponse,
    CatalogItemUpdate,
)
from app.services.catalog_service import (
    CatalogNotFoundError,
    catalog_item_to_response,
    create_catalog_item,
    delete_catalog_item,
    list_admin_items,
    list_catalog_category_options,
    search_public_items,
    update_catalog_item,
)

router = APIRouter()


@router.get("/categories")
async def list_catalog_categories():
    return list_catalog_category_options()


@router.get("/items", response_model=list[CatalogItemResponse])
async def list_public_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: CatalogCategory | None = None,
):
    items = await search_public_items(db, category=category)
    return [catalog_item_to_response(item) for item in items]


@router.get("/admin/items", response_model=list[CatalogItemAdminResponse])
async def list_admin_items_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
    internal_only: bool = Query(False),
):
    items = await list_admin_items(db, internal_only=internal_only)
    return [catalog_item_to_response(item, admin=True) for item in items]


@router.post("/admin/items", response_model=CatalogItemAdminResponse, status_code=201)
async def create_admin_item(
    data: CatalogItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    item = await create_catalog_item(db, data)
    return catalog_item_to_response(item, admin=True)


@router.patch("/admin/items/{item_id}", response_model=CatalogItemAdminResponse)
async def update_admin_item(
    item_id: int,
    data: CatalogItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    try:
        item = await update_catalog_item(db, item_id, data)
    except CatalogNotFoundError as exc:
        raise_http_for_service_error(exc)
    return catalog_item_to_response(item, admin=True)


@router.delete("/admin/items/{item_id}", status_code=204)
async def delete_admin_item(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    try:
        await delete_catalog_item(db, item_id)
    except CatalogNotFoundError as exc:
        raise_http_for_service_error(exc)

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import CatalogCategory, CatalogSource


class CatalogItemResponse(BaseModel):
    id: int
    name: str
    category: CatalogCategory
    category_label: str
    description: str | None
    phone: str | None
    external_url: str | None
    price_hint: str | None
    address: str | None
    source: CatalogSource
    is_internal: bool = False
    sort_order: int

    model_config = {"from_attributes": True}


class CatalogItemCreate(BaseModel):
    name: str = Field(min_length=3, max_length=300)
    category: CatalogCategory
    description: str | None = None
    phone: str | None = None
    external_url: str | None = None
    price_hint: str | None = None
    address: str | None = None
    is_internal: bool = True
    sort_order: int = 50


class CatalogItemUpdate(BaseModel):
    name: str | None = None
    category: CatalogCategory | None = None
    description: str | None = None
    phone: str | None = None
    external_url: str | None = None
    price_hint: str | None = None
    address: str | None = None
    is_internal: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class CatalogItemAdminResponse(CatalogItemResponse):
    is_active: bool
    seed_key: str | None
    created_at: datetime

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PlaceCategory, ShopComplaintType


class PlaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    category: PlaceCategory
    category_label: str = ""
    description: str | None
    address: str | None
    latitude: float
    longitude: float
    phone: str | None
    website: str | None
    opening_hours: str | None
    avg_rating: float
    review_count: int
    complaint_count: int
    last_synced_at: datetime | None


class PlaceDetailResponse(PlaceResponse):
    reviews: list["PlaceReviewResponse"] = []
    recent_complaints: list["PlaceComplaintResponse"] = []


class PlaceReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    text: str | None = Field(None, max_length=1000)
    author_name: str | None = Field(None, max_length=100)


class PlaceReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating: int
    text: str | None
    author_name: str | None
    created_at: datetime


class PlaceComplaintCreate(BaseModel):
    complaint_type: ShopComplaintType
    description: str = Field(min_length=10, max_length=2000)
    price_tagged: str | None = None
    price_charged: str | None = None
    receipt_info: str | None = None
    author_name: str | None = None


class PlaceComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_type: ShopComplaintType
    complaint_label: str = ""
    description: str
    price_tagged: str | None
    price_charged: str | None
    status: str
    created_at: datetime


class MapBoundsQuery(BaseModel):
    south: float
    west: float
    north: float
    east: float


class PlaceListResponse(BaseModel):
    items: list[PlaceResponse]
    total: int


class MapStatsResponse(BaseModel):
    total_places: int
    by_category: dict[str, int]
    last_sync: datetime | None
    center: dict[str, float]

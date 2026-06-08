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
    external_rating: float = 0.0
    external_review_count: int = 0
    display_rating: float = 0.0
    display_review_count: int = 0
    rating_source: str | None = None
    yandex_url: str | None = None
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
    total_reviews: int = 0
    total_complaints: int = 0
    active_complaints: int = 0
    avg_rating_by_category: dict[str, float] = Field(default_factory=dict)
    active_taxi_count: int = 0
    route_count: int = 0


class TaxiServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str
    phones_extra: str | None
    description: str | None
    is_24h: bool
    rating: float
    price_from: int | None

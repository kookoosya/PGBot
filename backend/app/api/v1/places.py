from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_optional_user, require_owner
from app.core.rate_limit import limiter
from app.database import get_db
from app.models.enums import (
    MAP_REPORT_LABELS,
    PLACE_CATEGORY_LABELS,
    SHOP_COMPLAINT_LABELS,
    PlaceCategory,
    ShopComplaintType,
)
from app.models.place import Place
from app.models.taxi import TaxiService
from app.models.user import User
from app.schemas.place import (
    MapStatsResponse,
    PlaceComplaintCreate,
    PlaceComplaintResponse,
    PlaceDetailResponse,
    PlaceListResponse,
    PlaceReviewCreate,
    PlaceReviewResponse,
    TaxiServiceResponse,
)
from app.services.map_routes import get_map_routes
from app.services.map_sync import sync_all_map_data
from app.services.osm_sync import seed_pushkin_landmarks, sync_places_from_osm
from app.services.place_service import (
    PlaceComplaintInput,
    PlaceNotFoundError,
    PlaceReviewInput,
    PlaceSearchParams,
    PlaceSortField,
    PlaceValidationError,
    add_place_review,
    build_complaint_response,
    build_place_response,
    create_place_complaint,
    get_map_stats,
    get_place_details,
    search_places,
)
from app.services.yandex_sync import sync_places_from_yandex

router = APIRouter()


@router.get("/categories")
async def list_place_categories():
    return [
        {"value": c.value, "label": PLACE_CATEGORY_LABELS[c]}
        for c in PlaceCategory
    ]


@router.get("/complaint-types")
async def list_complaint_types():
    return [
        {"value": t.value, "label": SHOP_COMPLAINT_LABELS[t]}
        for t in ShopComplaintType
        if t not in MAP_REPORT_LABELS
    ]


@router.get("/map-report-types")
async def list_map_report_types():
    return [{"value": t.value, "label": MAP_REPORT_LABELS[t]} for t in MAP_REPORT_LABELS]


@router.get("/routes")
async def list_map_routes():
    return get_map_routes()


@router.get("/taxi", response_model=list[TaxiServiceResponse])
async def list_taxi(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(TaxiService)
        .where(TaxiService.is_active.is_(True))
        .order_by(TaxiService.sort_order, TaxiService.rating.desc())
    )
    return [TaxiServiceResponse.model_validate(t) for t in result.scalars().all()]


@router.get("/map/stats", response_model=MapStatsResponse)
async def map_stats(db: Annotated[AsyncSession, Depends(get_db)]):
    stats = await get_map_stats(db)
    return stats.to_response()


@router.get("", response_model=PlaceListResponse)
async def list_places(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: PlaceCategory | None = None,
    search: str | None = Query(None, max_length=100),
    shops_only: bool = False,
    useful_only: bool = False,
    min_rating: float | None = Query(None, ge=0, le=5),
    south: float | None = None,
    west: float | None = None,
    north: float | None = None,
    east: float | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    sort: PlaceSortField = Query("rating"),
    district: bool = False,
):
    result = await search_places(
        db,
        PlaceSearchParams(
            category=category,
            search=search,
            shops_only=shops_only,
            useful_only=useful_only,
            min_rating=min_rating,
            south=south,
            west=west,
            north=north,
            east=east,
            page=page,
            page_size=page_size,
            sort_by=sort,
            district=district,
        ),
    )
    return PlaceListResponse(
        items=[build_place_response(place) for place in result.items],
        total=result.total,
    )


@router.get("/{place_id}", response_model=PlaceDetailResponse)
async def get_place(place_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        detail = await get_place_details(db, place_id)
    except PlaceNotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return detail.response


@router.post("/{place_id}/reviews", response_model=PlaceReviewResponse, status_code=201)
@limiter.limit("20/hour")
async def add_review(
    place_id: int,
    request: Request,
    data: PlaceReviewCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    try:
        result = await add_place_review(
            db,
            place_id,
            PlaceReviewInput(
                rating=data.rating,
                text=data.text,
                author_name=data.author_name,
            ),
            user=current_user,
        )
    except PlaceNotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except PlaceValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return PlaceReviewResponse.model_validate(result.review)


@router.post("/{place_id}/complaints", response_model=PlaceComplaintResponse, status_code=201)
@limiter.limit("10/hour")
async def add_complaint(
    place_id: int,
    request: Request,
    data: PlaceComplaintCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    try:
        result = await create_place_complaint(
            db,
            place_id,
            PlaceComplaintInput(
                complaint_type=data.complaint_type,
                description=data.description,
                price_tagged=data.price_tagged,
                price_charged=data.price_charged,
                receipt_info=data.receipt_info,
                author_name=data.author_name,
            ),
            user=current_user,
        )
    except PlaceNotFoundError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    except PlaceValidationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    return build_complaint_response(result.complaint)


@router.post("/sync")
async def sync_osm(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    result = await sync_places_from_osm(db)
    return result


@router.post("/sync-all")
async def sync_all(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    return await sync_all_map_data(db)


@router.post("/sync-yandex")
async def sync_yandex(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    return await sync_places_from_yandex(db)


@router.post("/seed")
async def seed_landmarks(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_owner())],
):
    count = await seed_pushkin_landmarks(db)
    return {"seeded": count}

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.deps import get_optional_user, require_roles
from app.database import get_db
from app.models.enums import (
    PLACE_CATEGORY_LABELS,
    SHOP_COMPLAINT_LABELS,
    IssueCategory,
    IssueStatus,
    PlaceCategory,
    Priority,
    ShopComplaintType,
    UserRole,
)
from app.models.issue import Issue
from app.models.place import Place, PlaceComplaint, PlaceReview
from app.models.user import User
from app.schemas.place import (
    MapStatsResponse,
    PlaceComplaintCreate,
    PlaceComplaintResponse,
    PlaceDetailResponse,
    PlaceListResponse,
    PlaceResponse,
    PlaceReviewCreate,
    PlaceReviewResponse,
)
from app.services.osm_sync import seed_pushkin_landmarks, sync_places_from_osm

router = APIRouter()
settings = get_settings()

SHOP_CATEGORIES = {
    PlaceCategory.SHOP, PlaceCategory.SUPERMARKET, PlaceCategory.PHARMACY,
}


def _place_response(p: Place) -> PlaceResponse:
    return PlaceResponse(
        id=p.id, name=p.name, category=p.category,
        category_label=PLACE_CATEGORY_LABELS.get(p.category, p.category),
        description=p.description, address=p.address,
        latitude=p.latitude, longitude=p.longitude,
        phone=p.phone, website=p.website, opening_hours=p.opening_hours,
        avg_rating=p.avg_rating, review_count=p.review_count,
        complaint_count=p.complaint_count, last_synced_at=p.last_synced_at,
    )


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
    ]


@router.get("/map/stats", response_model=MapStatsResponse)
async def map_stats(db: Annotated[AsyncSession, Depends(get_db)]):
    total = (await db.execute(select(func.count(Place.id)).where(Place.is_active.is_(True)))).scalar() or 0
    cat_result = await db.execute(
        select(Place.category, func.count(Place.id))
        .where(Place.is_active.is_(True))
        .group_by(Place.category)
    )
    by_cat = {PLACE_CATEGORY_LABELS.get(row[0], str(row[0])): row[1] for row in cat_result.all()}
    last = (await db.execute(select(func.max(Place.last_synced_at)))).scalar()
    return MapStatsResponse(
        total_places=total,
        by_category=by_cat,
        last_sync=last,
        center={"lat": settings.MAP_CENTER_LAT, "lng": settings.MAP_CENTER_LNG},
    )


@router.get("", response_model=PlaceListResponse)
async def list_places(
    db: Annotated[AsyncSession, Depends(get_db)],
    category: PlaceCategory | None = None,
    search: str | None = None,
    shops_only: bool = False,
    south: float | None = None,
    west: float | None = None,
    north: float | None = None,
    east: float | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    query = select(Place).where(Place.is_active.is_(True))
    if category:
        query = query.where(Place.category == category)
    if shops_only:
        query = query.where(Place.category.in_(SHOP_CATEGORIES))
    if search:
        query = query.where(Place.name.ilike(f"%{search}%"))
    if all(v is not None for v in (south, west, north, east)):
        query = query.where(
            Place.latitude >= south, Place.latitude <= north,
            Place.longitude >= west, Place.longitude <= east,
        )

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    query = query.order_by(Place.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    places = result.scalars().all()
    return PlaceListResponse(items=[_place_response(p) for p in places], total=total)


@router.get("/{place_id}", response_model=PlaceDetailResponse)
async def get_place(place_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Place)
        .options(selectinload(Place.reviews), selectinload(Place.complaints))
        .where(Place.id == place_id)
    )
    place = result.scalar_one_or_none()
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")

    reviews = sorted(place.reviews, key=lambda r: r.created_at, reverse=True)[:10]
    complaints = sorted(place.complaints, key=lambda c: c.created_at, reverse=True)[:5]

    resp = _place_response(place)
    return PlaceDetailResponse(
        **resp.model_dump(),
        reviews=[PlaceReviewResponse.model_validate(r) for r in reviews],
        recent_complaints=[
            PlaceComplaintResponse(
                id=c.id, complaint_type=c.complaint_type,
                complaint_label=SHOP_COMPLAINT_LABELS.get(c.complaint_type, c.complaint_type),
                description=c.description, price_tagged=c.price_tagged,
                price_charged=c.price_charged, status=c.status, created_at=c.created_at,
            )
            for c in complaints
        ],
    )


@router.post("/{place_id}/reviews", response_model=PlaceReviewResponse, status_code=201)
async def add_review(
    place_id: int,
    data: PlaceReviewCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    result = await db.execute(select(Place).where(Place.id == place_id))
    place = result.scalar_one_or_none()
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")

    review = PlaceReview(
        place_id=place_id,
        rating=data.rating,
        text=data.text,
        author_name=data.author_name or (current_user.full_name if current_user else "Житель"),
        user_id=current_user.id if current_user else None,
    )
    db.add(review)
    await db.flush()

    avg_result = await db.execute(
        select(func.avg(PlaceReview.rating), func.count(PlaceReview.id))
        .where(PlaceReview.place_id == place_id)
    )
    avg_row = avg_result.one()
    place.avg_rating = round(float(avg_row[0] or 0), 1)
    place.review_count = avg_row[1] or 0

    return PlaceReviewResponse.model_validate(review)


@router.post("/{place_id}/complaints", response_model=PlaceComplaintResponse, status_code=201)
async def add_complaint(
    place_id: int,
    data: PlaceComplaintCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
):
    result = await db.execute(select(Place).where(Place.id == place_id))
    place = result.scalar_one_or_none()
    if not place:
        raise HTTPException(status_code=404, detail="Место не найдено")

    complaint = PlaceComplaint(
        place_id=place_id,
        complaint_type=data.complaint_type,
        description=data.description,
        price_tagged=data.price_tagged,
        price_charged=data.price_charged,
        receipt_info=data.receipt_info,
        author_name=data.author_name or (current_user.full_name if current_user else "Житель"),
        user_id=current_user.id if current_user else None,
    )
    db.add(complaint)
    place.complaint_count += 1

    issue_desc = (
        f"Жалоба на {place.name} ({place.address or ''})\n"
        f"Тип: {SHOP_COMPLAINT_LABELS.get(data.complaint_type, data.complaint_type)}\n"
        f"{data.description}"
    )
    if data.price_tagged or data.price_charged:
        issue_desc += f"\nЦена на ценнике: {data.price_tagged or '—'}, на кассе: {data.price_charged or '—'}"

    issue = Issue(
        title=f"Жалоба: {place.name}",
        description=issue_desc,
        status=IssueStatus.NEW,
        category=IssueCategory.OTHER,
        priority=Priority.MEDIUM,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        resident_id=current_user.id if current_user else None,
    )
    db.add(issue)
    await db.flush()
    complaint.issue_id = issue.id

    return PlaceComplaintResponse(
        id=complaint.id, complaint_type=complaint.complaint_type,
        complaint_label=SHOP_COMPLAINT_LABELS.get(complaint.complaint_type, ""),
        description=complaint.description, price_tagged=complaint.price_tagged,
        price_charged=complaint.price_charged, status=complaint.status,
        created_at=complaint.created_at,
    )


@router.post("/sync")
async def sync_osm(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN))],
):
    result = await sync_places_from_osm(db)
    return result


@router.post("/seed")
async def seed_landmarks(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_roles(UserRole.SUPER_ADMIN))],
):
    count = await seed_pushkin_landmarks(db)
    return {"seeded": count}

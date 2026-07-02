"""Place API response mappers."""

from __future__ import annotations

from app.models.enums import MAP_REPORT_LABELS, PLACE_CATEGORY_LABELS, SHOP_COMPLAINT_LABELS
from app.models.place import Place, PlaceComplaint, PlaceReview
from app.schemas.place import (
    PlaceComplaintResponse,
    PlaceDetailResponse,
    PlaceResponse,
    PlaceReviewResponse,
)
from app.services.schedule import format_opening_hours

from app.services.place_inventory import verification_label

from .schemas import PlaceRatingMeta


def complaint_label(complaint: PlaceComplaint) -> str:
    return (
        MAP_REPORT_LABELS.get(complaint.complaint_type)
        or SHOP_COMPLAINT_LABELS.get(complaint.complaint_type, complaint.complaint_type)
    )


def build_complaint_response(
    complaint: PlaceComplaint,
    *,
    owner_notified: bool | None = None,
) -> PlaceComplaintResponse:
    """Map a ``PlaceComplaint`` ORM instance to ``PlaceComplaintResponse``."""
    return PlaceComplaintResponse(
        id=complaint.id,
        complaint_type=complaint.complaint_type,
        complaint_label=complaint_label(complaint),
        description=complaint.description,
        price_tagged=complaint.price_tagged,
        price_charged=complaint.price_charged,
        status=complaint.status,
        created_at=complaint.created_at,
        owner_notified=owner_notified,
    )


def place_rating_meta(place: Place) -> PlaceRatingMeta:
    """Return display rating fields for API responses."""
    if place.external_rating > 0:
        source = "yandex" if place.external_source == "yandex" else None
        return {
            "display_rating": place.external_rating,
            "display_review_count": place.external_review_count,
            "rating_source": source,
        }
    if place.avg_rating > 0:
        return {
            "display_rating": place.avg_rating,
            "display_review_count": place.review_count,
            "rating_source": "users",
        }
    return {"display_rating": 0.0, "display_review_count": 0, "rating_source": None}


def build_place_response(place: Place) -> PlaceResponse:
    """Map a ``Place`` ORM instance to ``PlaceResponse``."""
    meta = place_rating_meta(place)
    return PlaceResponse(
        id=place.id,
        name=place.name,
        category=place.category,
        category_label=PLACE_CATEGORY_LABELS.get(place.category, place.category),
        description=place.description,
        address=place.address,
        latitude=place.latitude,
        longitude=place.longitude,
        phone=place.phone,
        website=place.website,
        opening_hours=format_opening_hours(place.opening_hours) or place.opening_hours,
        avg_rating=place.avg_rating,
        review_count=place.review_count,
        external_rating=place.external_rating,
        external_review_count=place.external_review_count,
        yandex_url=place.yandex_url,
        complaint_count=place.complaint_count,
        last_synced_at=place.last_synced_at,
        scope=place.scope,
        verification_status=place.verification_status,
        verification_source_url=place.verification_source_url,
        verified_at=place.verified_at,
        verification_note=place.verification_note,
        verification_label=verification_label(place.verification_status),
        **meta,
    )


def build_place_detail_response(
    place: Place,
    *,
    reviews: list[PlaceReview],
    recent_complaints: list[PlaceComplaint],
) -> PlaceDetailResponse:
    """Build a full place detail payload for the API."""
    base = build_place_response(place)
    return PlaceDetailResponse(
        **base.model_dump(),
        reviews=[PlaceReviewResponse.model_validate(review) for review in reviews],
        recent_complaints=[
            PlaceComplaintResponse(
                id=complaint.id,
                complaint_type=complaint.complaint_type,
                complaint_label=complaint_label(complaint),
                description=complaint.description,
                price_tagged=complaint.price_tagged,
                price_charged=complaint.price_charged,
                status=complaint.status,
                created_at=complaint.created_at,
            )
            for complaint in recent_complaints
        ],
    )

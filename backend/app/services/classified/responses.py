"""API response mappers for classified ads."""

from __future__ import annotations

from app.models.classified import ClassifiedAd
from app.models.enums import CLASSIFIED_LABELS, ClassifiedCategory
from app.services.classified.schemas import ClassifiedCreateInput, ClassifiedSearchResult


def classified_to_response(ad: ClassifiedAd):
    from app.schemas.classified import ClassifiedResponse

    return ClassifiedResponse(
        id=ad.id,
        category=ad.category,
        category_label=CLASSIFIED_LABELS.get(ad.category, ad.category),
        title=ad.title,
        description=ad.description,
        price=ad.price,
        price_unit=ad.price_unit,
        phone=ad.phone,
        author_name=ad.author_name,
        address=ad.address,
        contact_telegram=ad.contact_telegram,
        views_count=ad.views_count,
        created_at=ad.created_at.isoformat(),
    )


def classified_to_mine_response(ad: ClassifiedAd):
    from app.schemas.classified import ClassifiedMineResponse

    return ClassifiedMineResponse(
        id=ad.id,
        category=ad.category,
        category_label=CLASSIFIED_LABELS.get(ad.category, ad.category),
        title=ad.title,
        description=ad.description,
        price=ad.price,
        price_unit=ad.price_unit,
        phone=ad.phone,
        author_name=ad.author_name,
        address=ad.address,
        contact_telegram=ad.contact_telegram,
        views_count=ad.views_count,
        created_at=ad.created_at.isoformat(),
        payment_status=ad.payment_status,
        payment_reference=ad.payment_reference,
        placement_fee=ad.placement_fee,
        contact_vk=ad.contact_vk,
        is_active=ad.is_active,
    )


def classified_to_pending_response(ad: ClassifiedAd):
    from app.schemas.classified import ClassifiedPendingResponse

    return ClassifiedPendingResponse(
        id=ad.id,
        category=ad.category,
        category_label=CLASSIFIED_LABELS.get(ad.category, ad.category),
        title=ad.title,
        description=ad.description,
        price=ad.price,
        price_unit=ad.price_unit,
        phone=ad.phone,
        author_name=ad.author_name,
        address=ad.address,
        contact_telegram=ad.contact_telegram,
        views_count=ad.views_count,
        created_at=ad.created_at.isoformat(),
        payment_status=ad.payment_status,
        payment_reference=ad.payment_reference,
        placement_fee=ad.placement_fee,
        contact_vk=ad.contact_vk,
    )


def build_classified_list_response(result: ClassifiedSearchResult):
    from app.schemas.classified import ClassifiedListResponse

    return ClassifiedListResponse(
        items=[classified_to_response(ad) for ad in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
        has_next=result.has_next,
        has_prev=result.has_prev,
    )


def list_classified_category_options() -> list[dict[str, str]]:
    return [{"value": category.value, "label": CLASSIFIED_LABELS[category]} for category in ClassifiedCategory]


def to_classified_create_input(data) -> ClassifiedCreateInput:
    return ClassifiedCreateInput(
        category=data.category,
        title=data.title,
        description=data.description,
        phone=data.phone,
        author_name=data.author_name,
        price=data.price,
        price_unit=data.price_unit,
        address=data.address,
        contact_telegram=data.contact_telegram,
        contact_vk=data.contact_vk,
        payment_confirmed=data.payment_confirmed,
        payment_reference=data.payment_reference,
        website_url=data.website_url,
        agree_rules=data.agree_rules,
    )

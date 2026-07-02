"""Справочник портала: curated inventory из docs/factual-integrity/stage-02-place-inventory.json.

Телефоны и часы публикуются только при подтверждённом статусе поля.
Отсутствие сайта не деактивирует организацию.
"""

from datetime import datetime, timezone

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.place import Place
from app.models.taxi import TaxiService
from app.services.place_inventory import (
    build_public_description,
    inventory_checked_at,
    inventory_village_places,
    parse_category,
)

# Нет подтверждённых первичных источников для такси на этапе 2.
TAXI_SEED: list[tuple] = []

# Явный список закрытых организаций — только с доказательством CLOSED_CONFIRMED.
CLOSED_STABLE_KEYS: frozenset[str] = frozenset()


def _place_key(stable_key: str) -> str:
    return f"ref_{stable_key}"


def _yandex_maps_url(lat: float, lng: float, name: str) -> str:
    from urllib.parse import quote
    return f"https://yandex.ru/maps/?pt={lng},{lat}&z=17&text={quote(name + ' Пушкинские Горы')}"


def _public_phone(entry: dict) -> str | None:
    if entry.get("phone_status") in (None, "UNVERIFIED"):
        return None
    return entry.get("phone")


def _public_hours(entry: dict) -> str | None:
    if entry.get("hours_status") in (None, "UNVERIFIED"):
        return None
    return entry.get("opening_hours")


async def seed_village_places(db: AsyncSession) -> int:
    active_keys: set[str] = set()
    count = 0
    now = inventory_checked_at()
    inventory = inventory_village_places()

    for entry in inventory:
        if not entry.get("seed_as_reference", True):
            continue
        stable_key = entry["stable_key"]
        key = _place_key(stable_key)
        active_keys.add(key)

        name = entry["public_name"]
        cat = parse_category(entry["category"])
        lat = float(entry["latitude"])
        lng = float(entry["longitude"])
        addr = entry.get("address")
        phone = _public_phone(entry)
        hours = _public_hours(entry)
        website = entry.get("website")
        y_url = entry.get("yandex_url") or _yandex_maps_url(lat, lng, name)
        description = build_public_description(entry)

        result = await db.execute(select(Place).where(Place.yandex_id == key))
        place = result.scalars().first()

        fields = dict(
            name=name,
            category=cat,
            latitude=lat,
            longitude=lng,
            address=addr,
            phone=phone,
            opening_hours=hours,
            description=description,
            website=website,
            external_rating=0,
            external_review_count=0,
            external_source="reference",
            yandex_url=y_url,
            scope=entry.get("scope"),
            verification_status=entry.get("existence_status"),
            verification_source_url=(entry.get("source_types") or [None])[0],
            verified_at=now,
            verification_note=entry.get("verification_note"),
            is_active=stable_key not in CLOSED_STABLE_KEYS,
            last_synced_at=now,
        )

        if place:
            for attr, value in fields.items():
                setattr(place, attr, value)
        else:
            db.add(Place(yandex_id=key, **fields))
            count += 1

    ref_result = await db.execute(select(Place).where(Place.yandex_id.like("ref_%")))
    for place in ref_result.scalars().all():
        if place.yandex_id and place.yandex_id not in active_keys:
            place.is_active = False

    await db.flush()
    return count


async def seed_taxi_services(db: AsyncSession) -> int:
    allowed = {row[0] for row in TAXI_SEED}
    count = 0
    for name, phone, extra, desc, is_24h, rating, price, order in TAXI_SEED:
        result = await db.execute(
            select(TaxiService).where(TaxiService.name == name).order_by(TaxiService.id)
        )
        existing = result.scalars().first()
        if existing:
            existing.phone = phone
            existing.phones_extra = extra
            existing.description = desc
            existing.is_24h = is_24h
            existing.rating = rating
            existing.price_from = price
            existing.sort_order = order
            existing.is_active = True
        else:
            db.add(TaxiService(
                name=name, phone=phone, phones_extra=extra, description=desc,
                is_24h=is_24h, rating=rating, price_from=price, sort_order=order,
            ))
            count += 1

    all_result = await db.execute(select(TaxiService))
    for taxi in all_result.scalars().all():
        if taxi.name not in allowed:
            taxi.is_active = False

    await db.flush()
    return count


# Back-compat for tests importing VILLAGE_PLACES length checks
VILLAGE_PLACES = [
    (
        e["public_name"],
        parse_category(e["category"]),
        e["latitude"],
        e["longitude"],
        e.get("address"),
        _public_phone(e),
        _public_hours(e),
        0,
        0,
        e.get("website"),
        e.get("verification_note"),
    )
    for e in inventory_village_places()
    if e.get("seed_as_reference", True)
]

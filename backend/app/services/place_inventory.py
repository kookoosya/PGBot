"""Stage-02 curated place inventory loader and seed helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models.enums import PlaceCategory

ACTIVE_DECISIONS = frozenset({"KEEP", "RESTORE"})


def _inventory_candidates() -> tuple[Path, ...]:
    here = Path(__file__).resolve()
    return (
        here.parents[1] / "data" / "stage-02-place-inventory.json",
        here.parents[3] / "docs" / "factual-integrity" / "stage-02-place-inventory.json",
        Path("/app/app/data/stage-02-place-inventory.json"),
    )


def _resolve_inventory_path() -> Path:
    for path in _inventory_candidates():
        if path.is_file():
            return path
    raise FileNotFoundError(
        "stage-02-place-inventory.json not found; expected backend/app/data/ or docs/factual-integrity/"
    )


@lru_cache(maxsize=1)
def load_place_inventory() -> list[dict[str, Any]]:
    with _resolve_inventory_path().open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return list(payload.get("places", []))


def inventory_village_places() -> list[dict[str, Any]]:
    """Curated entries intended for reference seed (village + nearby on map)."""
    return [
        entry
        for entry in load_place_inventory()
        if entry.get("decision") in ACTIVE_DECISIONS
        and entry.get("active_status") != "CLOSED_CONFIRMED"
        and entry.get("seed_as_reference", True)
    ]


def inventory_by_stable_key() -> dict[str, dict[str, Any]]:
    return {entry["stable_key"]: entry for entry in load_place_inventory()}


def parse_category(value: str) -> PlaceCategory:
    try:
        return PlaceCategory(value)
    except ValueError:
        return PlaceCategory.OTHER


_VERIFICATION_LABELS: dict[str, str] = {
    "OWNER_CONFIRMED": "Подтверждено владельцем",
    "YANDEX_ACTIVE": "Данные Яндекс Карт — уточняйте перед визитом",
    "TWO_GIS_ACTIVE": "Данные 2GIS — уточняйте перед визитом",
    "MULTISOURCE_CONFIRMED": "Данные подтверждены Яндекс Картами и 2GIS",
    "OFFICIAL_PRIMARY": "Официальный источник",
    "OFFICIAL_SOCIAL": "Официальная страница организации",
    "OSM_ACTIVE": "Данные OpenStreetMap",
    "COMMUNITY_CONFIRMED": "Подтверждено местным жителем",
    "CONFLICTING": "Данные источников различаются — уточняйте перед визитом",
    "UNVERIFIED": "Данные уточняются",
    "CLOSED_CONFIRMED": "Закрыто",
}


def verification_label(status: str | None) -> str:
    if not status:
        return _VERIFICATION_LABELS["UNVERIFIED"]
    return _VERIFICATION_LABELS.get(status, _VERIFICATION_LABELS["UNVERIFIED"])


ALLOWED_SOURCE_TYPES = frozenset({
    "OWNER",
    "YANDEX",
    "TWO_GIS",
    "OFFICIAL_WEBSITE",
    "CHAIN_STORE_LOCATOR",
    "GOVERNMENT_REGISTRY",
    "OFFICIAL_SOCIAL",
    "OSM",
    "COMMUNITY",
    "OFFICIAL_PRIMARY",
})


def entry_source_types(entry: dict[str, Any]) -> set[str]:
    return {src.get("type") for src in entry.get("sources") or [] if src.get("type")}


def primary_verification_url(entry: dict[str, Any]) -> str | None:
    priority = (
        "OWNER",
        "OFFICIAL_PRIMARY",
        "OFFICIAL_WEBSITE",
        "GOVERNMENT_REGISTRY",
        "YANDEX",
        "TWO_GIS",
        "OSM",
        "CHAIN_STORE_LOCATOR",
    )
    sources = entry.get("sources") or []
    by_type = {src["type"]: src for src in sources if src.get("type")}
    for type_ in priority:
        src = by_type.get(type_)
        if src and src.get("url"):
            return src["url"]
    legacy = entry.get("source_types") or []
    return legacy[0] if legacy else entry.get("yandex_url")


def build_public_description(entry: dict[str, Any]) -> str | None:
    parts: list[str] = []
    note = entry.get("verification_note")
    if note:
        parts.append(note)
    website = entry.get("website")
    if website:
        parts.append(f"Сайт: {website}")
    label = verification_label(entry.get("existence_status"))
    parts.append(label)
    return " · ".join(parts) if parts else label


def inventory_checked_at() -> datetime:
    raw = load_place_inventory()[0].get("source_checked_at") if load_place_inventory() else None
    if raw:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)

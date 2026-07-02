"""Stage 1 regression: map reference factual integrity."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.models.enums import PlaceCategory
from app.models.place import Place
from app.models.taxi import TaxiService
from app.services.map_routes import MONASTERY_NAME, get_map_routes
from app.services.place.responses import place_rating_meta
from app.services.pushkin_places_seed import TAXI_SEED, VILLAGE_PLACES, seed_taxi_services, seed_village_places

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_MAP_DIR = REPO_ROOT / "frontend" / "src" / "pages" / "map"
FRONTEND_PAGES_DIR = REPO_ROOT / "frontend" / "src" / "pages"

PUBLIC_MAP_FILES = (
    FRONTEND_PAGES_DIR / "Map.tsx",
    FRONTEND_MAP_DIR / "PlacesList.tsx",
    FRONTEND_MAP_DIR / "MapStatsRibbon.tsx",
    FRONTEND_MAP_DIR / "PlaceDetailPanel.tsx",
    FRONTEND_MAP_DIR / "hotlines.ts",
    FRONTEND_MAP_DIR / "HotlinesPanel.tsx",
    FRONTEND_MAP_DIR / "MapServicesTabs.tsx",
)

FORBIDDEN_PHONES = (
    "2-01-01",
    "2-02-02",
    "2-05-05",
    "2-06-06",
    "000-28-28",
    "997-90-00",
)

FORBIDDEN_PHONE_FULL = (
    "+7 (81146) 2-01-01",
    "+7 (81146) 2-02-02",
    "+7 (81146) 2-05-05",
    "+7 (81146) 2-06-06",
    "+7 (921) 000-28-28",
    "+7 (900) 997-90-00",
)

OLD_MONASTERY_NAME = "Свято-Успенская Пушкиногорская лавра"

VERIFIED_SEED_NAMES = {
    "Государственный музей-заповедник А. С. Пушкина «Михайловское»",
    "Свято-Успенский Святогорский мужской монастырь",
    'Филиал «Пушкиногорский» ГБУЗ ПО «Островская МБ»',
}


def _seed_rows_text() -> str:
    return " ".join(str(cell) for row in VILLAGE_PLACES for cell in row if cell is not None)


def test_active_seed_excludes_old_monastery_name():
    names = {row[0] for row in VILLAGE_PLACES}
    assert OLD_MONASTERY_NAME not in names
    assert "Свято-Успенский Святогорский мужской монастырь" in names


def test_active_seed_excludes_placeholder_phones():
    blob = _seed_rows_text()
    for phone in FORBIDDEN_PHONE_FULL:
        assert phone not in blob


@pytest.mark.parametrize("rel_path", PUBLIC_MAP_FILES, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_public_map_files_exclude_placeholder_phones(rel_path: Path):
    text = rel_path.read_text(encoding="utf-8")
    for phone in FORBIDDEN_PHONES:
        assert phone not in text, f"placeholder phone {phone} in {rel_path.name}"


@pytest.mark.parametrize("rel_path", PUBLIC_MAP_FILES, ids=lambda p: p.relative_to(REPO_ROOT).as_posix())
def test_public_map_files_exclude_old_monastery_name(rel_path: Path):
    text = rel_path.read_text(encoding="utf-8")
    assert OLD_MONASTERY_NAME not in text


def test_hotlines_exclude_unverified_placeholder_phones():
    text = (FRONTEND_MAP_DIR / "hotlines.ts").read_text(encoding="utf-8")
    for phone in FORBIDDEN_PHONE_FULL:
        assert phone not in text


def test_map_routes_use_official_monastery_name():
    routes_blob = str(get_map_routes())
    assert OLD_MONASTERY_NAME not in routes_blob
    assert MONASTERY_NAME in routes_blob
    assert routes_blob.count(MONASTERY_NAME) >= 3


def test_taxi_seed_is_empty():
    assert TAXI_SEED == []


def test_active_seed_has_only_three_verified_entries():
    assert len(VILLAGE_PLACES) == 3
    assert {row[0] for row in VILLAGE_PLACES} == VERIFIED_SEED_NAMES


def test_reference_without_rating_has_no_public_verification_source():
    place = Place(
        name="Свято-Успенский Святогорский мужской монастырь",
        category=PlaceCategory.CULTURE,
        latitude=57.0224228,
        longitude=28.9200652,
        external_source="reference",
        external_rating=0,
        external_review_count=0,
        avg_rating=0,
        review_count=0,
    )
    meta = place_rating_meta(place)
    assert meta["rating_source"] is None
    assert meta["display_rating"] == 0.0


def test_yandex_rating_keeps_yandex_source_only():
    place = Place(
        name="Пример",
        category=PlaceCategory.SHOP,
        latitude=57.0,
        longitude=28.9,
        external_source="yandex",
        external_rating=4.5,
        external_review_count=10,
    )
    meta = place_rating_meta(place)
    assert meta["rating_source"] == "yandex"


def test_reference_with_external_rating_does_not_emit_reference_source():
    place = Place(
        name="Пример",
        category=PlaceCategory.SHOP,
        latitude=57.0,
        longitude=28.9,
        external_source="reference",
        external_rating=4.2,
        external_review_count=3,
    )
    meta = place_rating_meta(place)
    assert meta["rating_source"] is None
    assert meta["display_rating"] == 4.2


@pytest.mark.postgres
async def test_seed_deactivates_stale_reference_place(db_session):
    stale = Place(
        name="МФЦ",
        category=PlaceCategory.GOVERNMENT,
        latitude=57.0262,
        longitude=28.9100,
        address="ул. Ленина, 10",
        phone="+7 (81146) 2-02-02",
        yandex_id="ref_stale_mfc_test",
        external_source="reference",
        is_active=True,
    )
    db_session.add(stale)
    await db_session.flush()

    await seed_village_places(db_session)
    await db_session.refresh(stale)

    assert stale.is_active is False


@pytest.mark.postgres
async def test_seed_deactivates_unverified_taxi(db_session):
    taxi = TaxiService(
        name="Наше такси",
        phone="+7 (921) 000-28-28",
        is_active=True,
        sort_order=1,
    )
    db_session.add(taxi)
    await db_session.flush()

    await seed_taxi_services(db_session)
    await db_session.refresh(taxi)

    assert taxi.is_active is False

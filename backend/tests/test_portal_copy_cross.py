"""Cross-check shared/portal_copy.json between backend and frontend."""

import json
from pathlib import Path

from app.constants import portal_copy as pc

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_JSON = REPO_ROOT / "shared" / "portal_copy.json"


def test_shared_json_exists():
    assert SHARED_JSON.is_file()


def test_backend_matches_shared_json_brand():
    data = json.loads(SHARED_JSON.read_text(encoding="utf-8"))
    assert pc.BRAND_KICKER == data["brand"]["kicker"]
    assert pc.BRAND_TAGLINE == data["brand"]["tagline"]
    assert pc.LANDING_HERO_LEAD == data["landing_hero"]["lead"]


def test_backend_matches_shared_json_issue_hints():
    data = json.loads(SHARED_JSON.read_text(encoding="utf-8"))
    assert pc.ISSUE_STATUS_HINTS == data["issue_status_hints"]
    assert pc.ISSUE_STATUS_EMOJI == data["issue_status_emoji"]


def test_backend_matches_shared_json_empty_states():
    data = json.loads(SHARED_JSON.read_text(encoding="utf-8"))
    assert pc.EMPTY_STATES == data["empty_states"]
    assert pc.EMPTY_STATES["classifieds"]["title"]


def test_shared_json_links_and_vk_nonempty():
    data = json.loads(SHARED_JSON.read_text(encoding="utf-8"))
    assert data["links"]["map"]
    assert data["vk"]["welcome_body"]


def test_backend_matches_shared_json_page_sections():
    data = json.loads(SHARED_JSON.read_text(encoding="utf-8"))
    assert pc.PAGE_SECTIONS == data["page_sections"]
    assert pc.PAGE_SECTIONS["events"]["title"]
    assert pc.PAGE_SECTIONS["signup"]["submitIdle"]


def test_backend_matches_shared_json_landing_sections():
    data = json.loads(SHARED_JSON.read_text(encoding="utf-8"))
    assert pc.LANDING_SECTIONS == data["landing_sections"]
    assert pc.LANDING_SECTIONS["pskov"]["title"] == pc.PAGE_SECTIONS["events"]["pskov"]["title"]

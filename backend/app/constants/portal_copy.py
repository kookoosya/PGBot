"""Тексты портала — загружаются из shared/portal_copy.json (единый источник с frontend)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COPY_CANDIDATES = (
    _REPO_ROOT / "shared" / "portal_copy.json",
    Path(__file__).resolve().parents[2] / "shared" / "portal_copy.json",
)


@lru_cache(maxsize=1)
def _load_copy() -> dict:
    for path in _COPY_CANDIDATES:
        if path.is_file():
            with path.open(encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError(
        "portal_copy.json not found; expected shared/portal_copy.json in repo or /app/shared/"
    )


def _vk(key: str) -> str:
    return str(_load_copy()["vk"][key])


def _link(key: str) -> str:
    return str(_load_copy()["links"][key])


_data = _load_copy()
_brand = _data["brand"]

BRAND_KICKER = _brand["kicker"]
BRAND_TAGLINE = _brand["tagline"]

# --- VK welcome / help ---
VK_WELCOME_BODY = _vk("welcome_body")
VK_HELP_BODY = _vk("help_body")

# --- Classifieds ---
CLASSIFIED_EMPTY_VK = _vk("classified_empty")
CLASSIFIED_APPROVED_VK = _vk("classified_approved")
CLASSIFIED_REJECTED_VK = _vk("classified_rejected")
CLASSIFIED_SUBMITTED_VK = _vk("classified_submitted")

# --- Issues / complaints ---
COMPLAINTS_INFO_VK = _vk("complaints_info")
ISSUE_ACCEPTED_VK = _vk("issue_accepted")
ISSUE_STATUS_CHANGED_VK = _vk("issue_status_changed")

ISSUE_STATUS_HINTS: dict[str, str] = dict(_data["issue_status_hints"])
ISSUE_STATUS_EMOJI: dict[str, str] = dict(_data["issue_status_emoji"])

# Deep link button labels
LINK_EVENTS = _link("events")
LINK_CLASSIFIEDS = _link("classifieds")
LINK_COMPLAINTS = _link("complaints")
LINK_CLASSIFIED = _link("classified")
LINK_SITE = _link("site")
LINK_MAP = _link("map")
LINK_SUBMIT_CLASSIFIED = _link("submit_classified")
LINK_SUBMIT_COMPLAINT = _link("submit_complaint")
LINK_CABINET = _link("cabinet")

#!/usr/bin/env python3
"""Check /api/v1/public/today for real cinema films (not miscategorized events)."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request

# Keep in sync with backend/app/services/event/cinema.py
_CULTURE_LIKE_TITLE_RE = re.compile(
    r"культурно-просветительн|мероприяти[ея]|петрушкин|спектакл|концерт|выставк|"
    r"праздник|фестиваль|экскурс|лекци|ярмарк|театр|музе[йя]|мастер[- ]класс|"
    r"постановк|игра\s*«",
    re.IGNORECASE,
)

_CINEMA_AFISHA_SOURCES = frozenset({
    "orbilet", "kinopskov", "mirage", "silver", "kudago", "timepad",
})

_GENERIC_CINEMA_TITLES = frozenset({
    "кино", "сеанс", "фильм", "киносеанс", "кинопоказ",
})


def _is_generic_title(title: str) -> bool:
    normalized = title.strip().lower()
    if normalized in _GENERIC_CINEMA_TITLES:
        return True
    return len(normalized) < 4


def is_real_cinema_event(event: dict) -> bool:
    if event.get("category") != "cinema":
        return False
    title = event.get("title") or ""
    if _CULTURE_LIKE_TITLE_RE.search(title):
        return False
    location = (event.get("location") or "").lower()
    if "планетар" in location or "планетар" in title.lower():
        return False
    genre = event.get("genre")
    source = (event.get("source") or "").strip().lower()
    if _is_generic_title(title) and not genre:
        return False
    if source in _CINEMA_AFISHA_SOURCES:
        return True
    if genre:
        return True
    if re.search(r'[«»"]', title):
        return True
    return False


def check_today_payload(data: dict, *, min_films: int = 1) -> tuple[bool, str]:
    events = data.get("upcoming_events") or []
    cinema = [e for e in events if is_real_cinema_event(e)]
    if len(cinema) >= min_films:
        titles = ", ".join(e.get("title", "?") for e in cinema[:5])
        return True, f"{len(cinema)} film(s): {titles}"
    misc = [e.get("title") for e in events if e.get("category") == "cinema" and not is_real_cinema_event(e)]
    detail = f"real={len(cinema)}, misc_cinema={len(misc)}"
    if misc:
        detail += f" (filtered: {', '.join(misc[:3])})"
    return False, detail


def fetch_json(url: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: smoke_check_cinema.py <API_TODAY_URL> [--min N] [--fixture FILE]", file=sys.stderr)
        return 1

    url = sys.argv[1]
    min_films = 1
    fixture = None
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--min" and i + 1 < len(args):
            min_films = int(args[i + 1])
            i += 2
        elif args[i] == "--fixture" and i + 1 < len(args):
            fixture = args[i + 1]
            i += 2
        else:
            i += 1

    try:
        if fixture:
            with open(fixture, encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = fetch_json(url)
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL cinema API: {exc}")
        return 1

    ok, msg = check_today_payload(data, min_films=min_films)
    if ok:
        print(f"OK   cinema block — {msg}")
        return 0
    print(f"FAIL cinema block — {msg}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

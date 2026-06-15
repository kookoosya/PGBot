#!/usr/bin/env python3
"""Smoke checks for critical API user flows (validation + schema)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def _fetch(url: str, *, method: str = "GET", data: dict | None = None, timeout: float = 20.0) -> tuple[int, dict | str]:
    headers = {"Accept": "application/json"}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def run_checks(api_base: str) -> list[str]:
    errors: list[str] = []
    api = api_base.rstrip("/")

    code, today = _fetch(f"{api}/public/today")
    if code != 200:
        errors.append(f"today HTTP {code}")
    elif isinstance(today, dict):
        for key in ("map", "upcoming_events", "updated_at"):
            if key not in today:
                errors.append(f"today missing {key}")
        if isinstance(today.get("map"), dict) and "total_places" not in today["map"]:
            errors.append("today.map missing total_places")
    else:
        errors.append("today response is not JSON")

    code, events = _fetch(f"{api}/public/events?{urllib.parse.urlencode({'search': 'концерт'})}")
    if code != 200:
        errors.append(f"events search HTTP {code}")
    elif not isinstance(events, dict) or "items" not in events:
        errors.append("events search missing items")

    code, _ = _fetch(f"{api}/issues", method="POST", data={"description": "abc"})
    if code != 422:
        errors.append(f"issue validation expected 422, got {code}")

    code, classified = _fetch(f"{api}/classifieds", method="POST", data={"title": "x"})
    if code not in (400, 422):
        errors.append(f"classified validation expected 400/422, got {code}")

    code, info = _fetch(f"{api}/public/info")
    if code != 200:
        errors.append(f"public/info HTTP {code}")
    elif isinstance(info, dict):
        for key in ("site_url", "vk_url", "map_url"):
            if key not in info:
                errors.append(f"public/info missing {key}")

    return errors


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173/api/v1"
    if not base.endswith("/api/v1"):
        base = base.rstrip("/") + "/api/v1"

    errors = run_checks(base)
    if errors:
        for err in errors:
            print(f"FAIL {err}")
        return 1

    print("OK   API user scenarios (today, events, validation)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

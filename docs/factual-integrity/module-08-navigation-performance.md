# Module 8 — Navigation performance

**Baseline SHA:** `ae6692361717259ae8af5d915a3583a8f4d2cb5c`  
**Audit date:** 2026-07-03

## Root cause (proven)

**`key={location.pathname}` on `<main className="page-fade-wrap">` in `PublicLayout.tsx`**

Each section switch destroyed and recreated the entire `<main>` outlet wrapper. Because `main` carries the `page-fade-wrap` class, the CSS animation `page-fade-in` (300ms, `opacity: 0` → `1`) restarted on every navigation. Users saw a blank/faded shell for ~300–500ms after the URL already changed, even when route chunks and API data were ready.

**Evidence:**
- Playwright probe on production (`scripts/module-08-probe.mjs`): after click → `/map`, `main` opacity was **0** at ~130ms; reached **1** only after **~510ms**.
- After fix on local preview: same transition shows `main` opacity **1** at **~143ms** (no fade restart).
- Vitest `PublicLayout.navigation.test.tsx`: with `key`, `main` DOM node identity changes on route change (fail-before); without `key`, same element persists (pass-after).

## Rejected hypotheses

| Hypothesis | Status | Notes |
|------------|--------|-------|
| A. Duplicate API fetch on navigation | REJECTED | `trackVisit` once per path; no parallel duplicate pattern traced as primary delay |
| B. Full app rerender | REJECTED | Only `Outlet` child swaps; layout shell stays mounted |
| C. Map background work | REJECTED | `MapPage` unmounts off `/map`; map API/listeners cleaned in `useMapPage` effects |
| D. Bundle blocking (first visit) | Secondary | Lazy chunks add first-visit delay but not 300ms fade on repeat visits |
| E. Synchronous storage | REJECTED | No blocking localStorage on route change traced |
| F. Listener leak | REJECTED | No growth observed in navigation cycles |
| G. Missing lazy loading | REJECTED | Routes already lazy in `App.tsx` |

## Fail-before trace

```
Click «Карта» → URL /map @ ~130ms
main opacity @ 130ms: 0.0   (page-fade-in restarted)
main opacity @ 280ms: 0.58
main opacity @ 510ms: 1.0
```

## Baseline measurements (production, ae66923)

| Metric | Главная → Карта | Карта → Афиша |
|--------|-----------------|---------------|
| Click → URL | 130 ms | 373 ms |
| Click → main opacity ≥ 0.9 | ~433 ms | ~640 ms |
| Fade restart | yes | yes |
| Duplicate API (navigation) | 0 traced | 0 traced |

## Failing regression test

`frontend/src/components/layout/PublicLayout.navigation.test.tsx` — **「keeps the same main element across route changes」** failed before fix (`main` node replaced when `key={location.pathname}` present).

## Fix (minimal)

Removed `key={location.pathname}` from `<main>` in `PublicLayout.tsx`.

React Router still unmounts/mounts route page components via `<Outlet>`. Map leaves `/map` correctly. Initial page fade on first load remains (single `main` mount). No router rewrite, no design change.

## Pass-after measurements (local preview, fix)

| Metric | До | После | Δ |
|--------|-----|-------|---|
| Click → URL | 130 ms | 143 ms | ~same |
| Click → main opacity ≥ 0.9 | ~433 ms | **143 ms** | **−67%** |
| Fade restart on tab switch | yes | **no** | fixed |
| Карта → Афиша click → URL | 373 ms | 163 ms | −56% |

## API requests

No change intended; navigation does not add duplicate fetches. Map/events refetch on remount unchanged (route component lifecycle).

## Render count / long tasks / listeners

Cannot be verified in CI jsdom; production Playwright long-task counts not captured in blocked full script run. Fade remount eliminated (proven via DOM identity + opacity trace).

## Manual verification checklist

Pending post-deploy production browser pass (20 cycles). Local: 10 vitest navigation cases pass.

## Cannot be verified (pre-deploy)

- Production pass-after opacity trace (requires deploy)
- Production 20-cycle manual matrix (desktop/mobile/throttled)
- Screenshots `docs/screenshots/module-08-deploy/*.png`
- CI run ID
- `/health git_commit` for final SHA

## Module 9

**NOT STARTED.**

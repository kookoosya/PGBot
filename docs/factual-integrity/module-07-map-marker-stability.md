# Module 7 — Map marker stability audit

**Baseline:** `ec679f1d97d3a270cd94d2185c2951e750cf3a18`  
**Audit date:** 2026-07-03

## Fail-before scenario

1. User opens map, filters «Супермаркет».
2. Fast zoom-in sends request **A** (tighter bbox, fewer places).
3. Quick zoom-out/pan sends request **B** (wider bbox).
4. Response **B** arrives first → markers correct.
5. Stale response **A** arrives last → `setPlaces` overwrites with fewer IDs → markers disappear inside viewport.

**Example:** «Магнит» (57.03, 28.92) visible after zoom-out; stale zoom-in response removes it.

## Root cause (proven)

**Request race (A):** `useMapPage.loadPlaces` had no `AbortController` and no request sequence guard. Any late response unconditionally called `setPlaces`.

## Hypotheses not confirmed as primary cause

| Hypothesis | Status |
|------------|--------|
| Bbox without padding | Secondary — added 6% padding as edge stabilizer |
| ClusterLayer cleanup flash | Minor — removed redundant `clearLayers` on effect cleanup |
| page_size too small | Not proven |
| Backend bbox bug | Not changed — exact filter unchanged |

## Fix (minimal)

1. `createPlacesRequestController()` — abort previous fetch, monotonic request id.
2. Apply `setPlaces` / `setPlacesError` / `setPlacesLoading` only when `isLatest(requestId)`.
3. Ignore `AbortError` (no user-facing error).
4. `padMapBounds` (6%) centralized in `boundsToQueryParams`.
5. `ClusterLayer` — no cleanup `clearLayers` between place updates.

## Tests

- `mapPlacesRequest.test.ts` — fail-before unguarded vs pass-after guarded
- `useMapPage.places.test.ts` — stale response, abort, loading retention, category param

## Module 8

**NOT STARTED.**

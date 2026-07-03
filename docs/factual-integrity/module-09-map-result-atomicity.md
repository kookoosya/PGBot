# Module 9 — map result atomicity

**Baseline SHA:** `e197a177528989a5b85619028a21125ba9613ae2`  
**Date:** 2026-07-03

## Fail-before

### A — filter transient
При смене категории `hasActiveFilter` и подпись менялись сразу, а `placesTotal` / `places` — только после ответа API.  
Состояние: **новый фильтр + старый count (45) + старые markers** до ~2 с.

### B — mobile 30 vs 29
`response.total` и `currentAreaCount` считали организации в **padded** bbox (Module 7, +6%).  
Одна точка попадала в buffer, но не в exact viewport → loaded=30, visible=29.  
ClusterLayer получал все loaded markers; расхождение было в **displayed count**, не в потере ID.

### C — list DOM
Стабильного `data-place-id` не было; headless-верификация не могла сравнить list IDs.

## Root cause

1. **Filter change:** count и items обновлялись неатомарно относительно filterKey; UI показывал несовместимый snapshot.
2. **Visible vs loaded:** count брал `response.total` (padded), а не exact bounds filter.
3. **List IDs:** отсутствовал атрибут для верификации.

## Rejected hypotheses

- Backend count defect — **нет** (frontend-only).
- ClusterLayer теряет ID — **не доказано**; расхождение из padded vs exact.
- Duplicate IDs — **не обнаружено** в тестах.

## Fix

### `mapResultSnapshot.ts`
- `buildPlacesFilterKey`, `filterPlacesInBounds`, `deriveVisiblePlaces`
- `isIncompatibleFilterLoading` — filter change во время loading
- При bbox-only loading: freeze visible bounds на snapshot.exactBounds (Module 7)

### `useMapPage.ts`
- Атомарный `PlacesResultSnapshot` (requestId, filterKey, exactBounds, items)
- `visiblePlaces` / `visibleCount` для UI и списка
- `clusterPlaces` = loaded items (padded); очищается при incompatible filter load
- Incompatible filter: «Обновляем список…», count=null, places=[]

### UI
- «В видимой области: M» / «По фильтру в видимой области: M»
- `data-place-id` на строках списка

## Tests

- `mapResultSnapshot.test.ts` — bounds, filter key, 30/29 scenario
- `useMapPage.places.test.ts` — filter transient, bbox stability, padded buffer
- `mapCountConsistency.test.tsx` — новые тексты, loading state, data-place-id

## Cannot be verified (pre-deploy)

- Production cluster DOM sum vs visible IDs in headless
- Exact missing place ID on production mobile without live API trace

## Module 10

**NOT STARTED.**

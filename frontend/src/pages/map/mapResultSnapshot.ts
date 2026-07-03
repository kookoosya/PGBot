import type { Place } from "@/lib/api/types/places";

import type { MapBounds } from "./mapPlacesRequest";

export type PlacesFilterKey = string;

export type PlacesResultSnapshot = {
  requestId: number;
  filterKey: PlacesFilterKey;
  exactBounds: MapBounds | null;
  items: Place[];
};

export function buildPlacesFilterKey(opts: {
  category: string;
  shopsOnly: boolean;
  usefulOnly: boolean;
  search: string;
  isLodging: boolean;
}): PlacesFilterKey {
  if (opts.isLodging) return "lodging";
  return [
    opts.category || "-",
    opts.shopsOnly ? "shops" : "",
    opts.usefulOnly ? "useful" : "",
    opts.search || "",
  ].join("|");
}

export function isCoordinateInBounds(
  latitude: number,
  longitude: number,
  bounds: MapBounds,
): boolean {
  return latitude >= bounds.south
    && latitude <= bounds.north
    && longitude >= bounds.west
    && longitude <= bounds.east;
}

export function filterPlacesInBounds(places: Place[], bounds: MapBounds): Place[] {
  return places.filter((p) => isCoordinateInBounds(p.latitude, p.longitude, bounds));
}

export function resolveVisibleBounds(
  loading: boolean,
  snapshot: PlacesResultSnapshot | null,
  currentFilterKey: PlacesFilterKey,
  currentExactBounds: MapBounds | null,
): MapBounds | null {
  if (!snapshot) return null;
  if (snapshot.filterKey !== currentFilterKey) return null;
  if (snapshot.filterKey === "lodging") return null;
  if (loading) return snapshot.exactBounds;
  return currentExactBounds ?? snapshot.exactBounds;
}

export function deriveVisiblePlaces(
  snapshot: PlacesResultSnapshot | null,
  currentFilterKey: PlacesFilterKey,
  loading: boolean,
  currentExactBounds: MapBounds | null,
): Place[] {
  if (!snapshot || snapshot.filterKey !== currentFilterKey) return [];
  if (snapshot.filterKey === "lodging") return snapshot.items;
  const bounds = resolveVisibleBounds(loading, snapshot, currentFilterKey, currentExactBounds);
  if (!bounds) return snapshot.items;
  return filterPlacesInBounds(snapshot.items, bounds);
}

export function isSnapshotFilterCompatible(
  snapshot: PlacesResultSnapshot | null,
  currentFilterKey: PlacesFilterKey,
): boolean {
  return Boolean(snapshot && snapshot.filterKey === currentFilterKey);
}

export function isIncompatibleFilterLoading(
  loading: boolean,
  snapshot: PlacesResultSnapshot | null,
  currentFilterKey: PlacesFilterKey,
): boolean {
  return loading && !isSnapshotFilterCompatible(snapshot, currentFilterKey);
}

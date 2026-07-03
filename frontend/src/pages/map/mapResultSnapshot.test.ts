import { describe, expect, it } from "vitest";

import type { Place } from "@/lib/api/types/places";

import {
  buildPlacesFilterKey,
  deriveVisiblePlaces,
  filterPlacesInBounds,
  isCoordinateInBounds,
  isIncompatibleFilterLoading,
  isSnapshotFilterCompatible,
  resolveVisibleBounds,
} from "./mapResultSnapshot";
import type { MapBounds } from "./mapPlacesRequest";
import { padMapBounds } from "./mapPlacesRequest";

const EXACT: MapBounds = { south: 57.02, west: 28.9, north: 57.04, east: 28.95 };

const place = (id: number, lat: number, lng: number): Place => ({
  id,
  name: `Place ${id}`,
  category: "cafe",
  category_label: "Кафе",
  description: null,
  address: "",
  latitude: lat,
  longitude: lng,
  phone: null,
  website: null,
  opening_hours: null,
  avg_rating: 0,
  review_count: 0,
  external_rating: 0,
  external_review_count: 0,
  display_rating: 0,
  display_review_count: 0,
  rating_source: null,
  yandex_url: null,
  complaint_count: 0,
});

describe("mapResultSnapshot", () => {
  it("buildPlacesFilterKey distinguishes category and search", () => {
    expect(buildPlacesFilterKey({
      category: "supermarket",
      shopsOnly: false,
      usefulOnly: false,
      search: "",
      isLodging: false,
    })).toBe("supermarket|||");
    expect(buildPlacesFilterKey({
      category: "",
      shopsOnly: false,
      usefulOnly: false,
      search: "аптека",
      isLodging: false,
    })).toBe("-|||аптека");
    expect(buildPlacesFilterKey({
      category: "hotel",
      shopsOnly: false,
      usefulOnly: false,
      search: "",
      isLodging: true,
    })).toBe("lodging");
  });

  it("padded bounds are wider than exact bounds", () => {
    const padded = padMapBounds(EXACT);
    expect(padded.south).toBeLessThan(EXACT.south);
    expect(padded.north).toBeGreaterThan(EXACT.north);
    expect(padded.west).toBeLessThan(EXACT.west);
    expect(padded.east).toBeGreaterThan(EXACT.east);
  });

  it("excludes buffer-only point from visiblePlaces", () => {
    const padded = padMapBounds(EXACT);
    const inside = place(1, (EXACT.south + EXACT.north) / 2, (EXACT.west + EXACT.east) / 2);
    const bufferOnly = place(2, padded.south + 0.0001, EXACT.west);
    expect(isCoordinateInBounds(bufferOnly.latitude, bufferOnly.longitude, padded)).toBe(true);
    expect(isCoordinateInBounds(bufferOnly.latitude, bufferOnly.longitude, EXACT)).toBe(false);
    const visible = filterPlacesInBounds([inside, bufferOnly], EXACT);
    expect(visible.map((p) => p.id)).toEqual([1]);
  });

  it("keeps snapshot bounds during bbox-only loading", () => {
    const oldBounds: MapBounds = { south: 57.02, west: 28.9, north: 57.04, east: 28.95 };
    const newBounds: MapBounds = { south: 57.03, west: 28.91, north: 57.05, east: 28.96 };
    const key = "supermarket|||";
    const snapshot = {
      requestId: 1,
      filterKey: key,
      exactBounds: oldBounds,
      items: [place(1, 57.03, 28.92), place(2, 57.021, 28.901)],
    };
    expect(resolveVisibleBounds(true, snapshot, key, newBounds)).toEqual(oldBounds);
    expect(resolveVisibleBounds(false, snapshot, key, newBounds)).toEqual(newBounds);
  });

  it("marks incompatible filter loading when filterKey changes", () => {
    const snapshot = {
      requestId: 1,
      filterKey: "-|||",
      exactBounds: EXACT,
      items: [place(1, 57.03, 28.92)],
    };
    expect(isSnapshotFilterCompatible(snapshot, "supermarket|||")).toBe(false);
    expect(isIncompatibleFilterLoading(true, snapshot, "supermarket|||")).toBe(true);
    expect(isIncompatibleFilterLoading(true, snapshot, "-|||")).toBe(false);
  });

  it("deriveVisiblePlaces reproduces mobile 30 loaded vs 29 visible scenario", () => {
    const padded = padMapBounds(EXACT);
    const inside = place(1, 57.03, 28.92);
    const bufferOnly = place(2, padded.south + 0.0001, (EXACT.west + EXACT.east) / 2);
    const key = "-|||";
    const snapshot = {
      requestId: 1,
      filterKey: key,
      exactBounds: EXACT,
      items: Array.from({ length: 28 }, (_, i) => place(i + 10, 57.03, 28.92 + i * 0.0001))
        .concat([inside, bufferOnly]),
    };
    expect(snapshot.items).toHaveLength(30);
    const visible = deriveVisiblePlaces(snapshot, key, false, EXACT);
    expect(visible).toHaveLength(29);
  });
});

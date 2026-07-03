/**
 * @vitest-environment jsdom
 */
import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Place } from "@/lib/api/types/places";

import { padMapBounds } from "./mapPlacesRequest";
import { useMapPage } from "./useMapPage";

const placeA: Place = {
  id: 1,
  name: "Магнит",
  category: "supermarket",
  category_label: "Супермаркет",
  description: null,
  address: "ул. Ленина, 1",
  latitude: 57.03,
  longitude: 28.92,
  phone: null,
  website: null,
  opening_hours: null,
  avg_rating: 4.2,
  review_count: 3,
  external_rating: 0,
  external_review_count: 0,
  display_rating: 4.2,
  display_review_count: 3,
  rating_source: null,
  yandex_url: null,
  complaint_count: 0,
};

const placeB: Place = {
  ...placeA,
  id: 2,
  name: "Пятёрочка",
  latitude: 57.031,
  longitude: 28.921,
};

const bounds = { south: 57.02, west: 28.9, north: 57.04, east: 28.95 };

const { getPlaces } = vi.hoisted(() => ({
  getPlaces: vi.fn(),
}));

vi.mock("@/lib/api/index", () => ({
  api: {
    getPlaces,
    getComplaintTypes: vi.fn().mockResolvedValue([]),
    getMapReportTypes: vi.fn().mockResolvedValue([]),
    getPlaceCategories: vi.fn().mockResolvedValue([]),
    getTaxiServices: vi.fn().mockResolvedValue([]),
    getMapFilterModes: vi.fn().mockResolvedValue([]),
    getMapRoutes: vi.fn().mockResolvedValue([]),
    getMapStats: vi.fn().mockResolvedValue({
      total_places: 1,
      by_category: {},
      last_sync: null,
      center: { lat: 57.03, lng: 28.92 },
    }),
  },
}));

vi.mock("@/lib/offlineMap", () => ({
  cachePlacesForOffline: vi.fn(),
  downloadOfflineMapPack: vi.fn(),
  getOfflinePlaces: vi.fn(() => []),
  isOfflineMapReady: vi.fn(() => false),
  offlineBundleAge: vi.fn(() => null),
  registerServiceWorker: vi.fn(),
}));

describe("useMapPage places loading", () => {
  beforeEach(() => {
    getPlaces.mockReset();
    getPlaces.mockResolvedValue({ items: [placeA], total: 1 });
  });

  it("ignores stale response when newer map request finishes first", async () => {
    let resolveFirst: (value: { items: Place[]; total: number }) => void;
    let resolveSecond: (value: { items: Place[]; total: number }) => void;
    const first = new Promise<{ items: Place[]; total: number }>((resolve) => {
      resolveFirst = resolve;
    });
    const second = new Promise<{ items: Place[]; total: number }>((resolve) => {
      resolveSecond = resolve;
    });
    let call = 0;
    getPlaces.mockImplementation(() => {
      call += 1;
      return call === 1 ? first : second;
    });

    const { result } = renderHook(() => useMapPage());

    act(() => {
      result.current.loadPlaces(bounds);
      result.current.loadPlaces({ ...bounds, north: 57.035 });
    });

    await act(async () => {
      resolveSecond!({ items: [placeB], total: 1 });
    });
    await waitFor(() => expect(result.current.places.map((p) => p.id)).toEqual([2]));

    await act(async () => {
      resolveFirst!({ items: [placeA], total: 1 });
    });
    expect(result.current.places.map((p) => p.id)).toEqual([2]);
    expect(result.current.currentAreaCount).toBe(1);
  });

  it("updates visible count from latest snapshot items, not response.total", async () => {
    let resolveFirst: (value: { items: Place[]; total: number }) => void;
    let resolveSecond: (value: { items: Place[]; total: number }) => void;
    const first = new Promise<{ items: Place[]; total: number }>((resolve) => {
      resolveFirst = resolve;
    });
    const second = new Promise<{ items: Place[]; total: number }>((resolve) => {
      resolveSecond = resolve;
    });
    let call = 0;
    getPlaces.mockImplementation(() => {
      call += 1;
      return call === 1 ? first : second;
    });

    const { result } = renderHook(() => useMapPage());

    act(() => {
      result.current.loadPlaces(bounds);
      result.current.loadPlaces({ ...bounds, north: 57.035 });
    });

    await act(async () => {
      resolveSecond!({ items: [placeA, placeB], total: 99 });
    });
    await waitFor(() => expect(result.current.currentAreaCount).toBe(2));

    await act(async () => {
      resolveFirst!({ items: [placeA], total: 99 });
    });
    expect(result.current.currentAreaCount).toBe(2);
  });

  it("does not clear visible count on AbortError", async () => {
    let rejectSecond: (reason: unknown) => void;
    const second = new Promise<{ items: Place[]; total: number }>((_, reject) => {
      rejectSecond = reject;
    });
    let call = 0;
    getPlaces.mockImplementation(() => {
      call += 1;
      if (call === 1) return Promise.resolve({ items: [placeA], total: 1 });
      if (call === 2) return second;
      return Promise.resolve({ items: [placeB], total: 1 });
    });

    const { result } = renderHook(() => useMapPage());

    act(() => {
      result.current.loadPlaces(bounds);
    });
    await waitFor(() => expect(result.current.places).toHaveLength(1));

    act(() => {
      result.current.loadPlaces(bounds);
      result.current.loadPlaces(bounds);
    });

    await act(async () => {
      rejectSecond!(new DOMException("Aborted", "AbortError"));
    });

    expect(result.current.placesError).toBe(false);
    expect(result.current.currentAreaCount).toBe(1);
  });

  it("keeps previous places while newer bbox request is loading", async () => {
    let resolveSecond: (value: { items: Place[]; total: number }) => void;
    const second = new Promise<{ items: Place[]; total: number }>((resolve) => {
      resolveSecond = resolve;
    });
    let call = 0;
    getPlaces.mockImplementation(() => {
      call += 1;
      if (call === 1) return Promise.resolve({ items: [placeA], total: 1 });
      return second;
    });

    const { result } = renderHook(() => useMapPage());

    act(() => {
      result.current.loadPlaces(bounds);
    });
    await waitFor(() => expect(result.current.places).toHaveLength(1));

    act(() => {
      result.current.loadPlaces({ ...bounds, north: 57.035 });
    });

    expect(result.current.places).toHaveLength(1);
    expect(result.current.placesLoading).toBe(true);
    expect(result.current.incompatibleFilterLoading).toBe(false);
    expect(result.current.currentAreaCount).toBe(1);
    expect(result.current.clusterPlaces).toHaveLength(1);

    await act(async () => {
      resolveSecond!({ items: [placeA, placeB], total: 2 });
    });
    await waitFor(() => expect(result.current.places).toHaveLength(2));
    expect(result.current.currentAreaCount).toBe(2);
  });

  it("hides stale count and places when filter changes before response", async () => {
    let resolveSecond: (value: { items: Place[]; total: number }) => void;
    const second = new Promise<{ items: Place[]; total: number }>((resolve) => {
      resolveSecond = resolve;
    });
    let call = 0;
    getPlaces.mockImplementation(() => {
      call += 1;
      if (call === 1) return Promise.resolve({ items: [placeA, placeB], total: 2 });
      return second;
    });

    const { result } = renderHook(() => useMapPage());

    act(() => {
      result.current.loadPlaces(bounds);
    });
    await waitFor(() => expect(result.current.places).toHaveLength(2));
    expect(result.current.currentAreaCount).toBe(2);

    act(() => {
      result.current.applyCategoryFilter("supermarket");
    });

    expect(result.current.incompatibleFilterLoading).toBe(true);
    expect(result.current.currentAreaCount).toBeNull();
    expect(result.current.places).toHaveLength(0);
    expect(result.current.clusterPlaces).toHaveLength(0);

    await act(async () => {
      resolveSecond!({ items: [placeA], total: 1 });
    });
    await waitFor(() => expect(result.current.incompatibleFilterLoading).toBe(false));
    expect(result.current.places.map((p) => p.id)).toEqual([1]);
    expect(result.current.currentAreaCount).toBe(1);
    expect(result.current.clusterPlaces.map((p) => p.id)).toEqual([1]);
  });

  it("excludes padded-buffer-only places from visible count", async () => {
    const padded = padMapBounds(bounds);
    const bufferOnly: Place = {
      ...placeA,
      id: 99,
      latitude: padded.south + 0.0001,
      longitude: 28.92,
    };
    getPlaces.mockResolvedValueOnce({ items: [placeA, bufferOnly], total: 2 });

    const { result } = renderHook(() => useMapPage());
    act(() => {
      result.current.loadPlaces(bounds);
    });
    await waitFor(() => expect(result.current.places).toHaveLength(1));
    expect(result.current.currentAreaCount).toBe(1);
    expect(result.current.clusterPlaces).toHaveLength(2);
  });

  it("passes category filter on every request", async () => {
    const { result } = renderHook(() => useMapPage());

    act(() => {
      result.current.applyCategoryFilter("supermarket");
      result.current.loadPlaces(bounds);
    });

    await waitFor(() => {
      expect(getPlaces).toHaveBeenCalledWith(
        expect.objectContaining({ category: "supermarket" }),
        expect.objectContaining({ signal: expect.any(AbortSignal) }),
      );
    });
  });
});

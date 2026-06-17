import { describe, expect, it, beforeEach } from "vitest";
import {
  OFFLINE_TILE_CACHE,
  cachePlacesForOffline,
  clearOfflineBundle,
  getOfflinePlaces,
  isOfflineMapReady,
  loadOfflineBundle,
  offlineBundleAge,
  saveOfflineBundle,
} from "./offlineMap";
import type { Place } from "@/lib/api/types/places";
const storage = new Map<string, string>();

function mockLocalStorage() {
  Object.defineProperty(globalThis, "localStorage", {
    configurable: true,
    value: {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
      clear: () => storage.clear(),
    },
  });
}

const samplePlace = (id: number): Place =>
  ({
    id,
    name: `Place ${id}`,
    category: "shop",
    latitude: 57.02,
    longitude: 28.91,
    display_rating: 4,
    display_review_count: 1,
    rating_source: "internal",
  }) as Place;

describe("offlineMap", () => {
  beforeEach(() => {
    storage.clear();
    mockLocalStorage();
  });

  it("exports tile cache name aligned with service worker", () => {
    expect(OFFLINE_TILE_CACHE).toBe("pgbot-map-tiles-v8");
  });

  it("saves and loads offline bundle", () => {
    saveOfflineBundle({
      places: [samplePlace(1)],
      savedAt: "2026-06-16T12:00:00.000Z",
      center: { lat: 57.02, lng: 28.91 },
    });
    const bundle = loadOfflineBundle();
    expect(bundle?.places).toHaveLength(1);
    expect(bundle?.places[0].id).toBe(1);
  });

  it("returns null for missing bundle", () => {
    expect(loadOfflineBundle()).toBeNull();
  });

  it("tracks bundle age", () => {
    saveOfflineBundle({
      places: [],
      savedAt: "2026-06-16T12:00:00.000Z",
      center: { lat: 57.02, lng: 28.91 },
    });
    expect(offlineBundleAge()).toBe("2026-06-16T12:00:00.000Z");
  });

  it("clears offline bundle", () => {
    cachePlacesForOffline([samplePlace(2)]);
    clearOfflineBundle();
    expect(loadOfflineBundle()).toBeNull();
    expect(offlineBundleAge()).toBeNull();
  });

  it("merges places when caching", () => {
    cachePlacesForOffline([samplePlace(1)]);
    cachePlacesForOffline([samplePlace(2)]);
    const ids = getOfflinePlaces().map((p) => p.id).sort();
    expect(ids).toEqual([1, 2]);
  });

  it("reports ready only when flag and bundle exist", () => {
    cachePlacesForOffline([samplePlace(1)]);
    expect(isOfflineMapReady()).toBe(false);
    localStorage.setItem("pgbot_map_offline_ready", "1");
    expect(isOfflineMapReady()).toBe(true);
  });

  it("getOfflinePlaces returns empty without bundle", () => {
    expect(getOfflinePlaces()).toEqual([]);
  });
});

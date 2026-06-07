import type { Place } from "./api";

const CACHE_KEY = "pgbot_map_offline_v1";
const CACHE_TS_KEY = "pgbot_map_offline_ts";
const READY_KEY = "pgbot_map_offline_ready";

/** Район Пушкиногорья для кэша тайлов */
const DISTRICT_BOUNDS = {
  south: 56.89,
  west: 28.72,
  north: 57.16,
  east: 29.1,
};

export interface OfflineMapBundle {
  places: Place[];
  savedAt: string;
  center: { lat: number; lng: number };
}

export function saveOfflineBundle(bundle: OfflineMapBundle): void {
  localStorage.setItem(CACHE_KEY, JSON.stringify(bundle));
  localStorage.setItem(CACHE_TS_KEY, bundle.savedAt);
}

export function loadOfflineBundle(): OfflineMapBundle | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as OfflineMapBundle;
  } catch {
    return null;
  }
}

export function clearOfflineBundle(): void {
  localStorage.removeItem(CACHE_KEY);
  localStorage.removeItem(CACHE_TS_KEY);
}

export function offlineBundleAge(): string | null {
  return localStorage.getItem(CACHE_TS_KEY);
}

export function isOfflineMapReady(): boolean {
  return localStorage.getItem(READY_KEY) === "1" && loadOfflineBundle() !== null;
}

export function cachePlacesForOffline(places: Place[]): void {
  const prev = loadOfflineBundle();
  const merged = new Map<number, Place>();
  for (const p of prev?.places ?? []) merged.set(p.id, p);
  for (const p of places) merged.set(p.id, p);
  saveOfflineBundle({
    places: [...merged.values()],
    savedAt: new Date().toISOString(),
    center: { lat: 57.0267, lng: 28.91 },
  });
}

export function getOfflinePlaces(): Place[] {
  return loadOfflineBundle()?.places ?? [];
}

export async function downloadOfflineMapPack(places: Place[]): Promise<number> {
  cachePlacesForOffline(places);
  const tiles = await prefetchMapTiles(
    DISTRICT_BOUNDS.south,
    DISTRICT_BOUNDS.west,
    DISTRICT_BOUNDS.north,
    DISTRICT_BOUNDS.east,
    [12, 13, 14, 15, 16],
  );
  localStorage.setItem(READY_KEY, "1");
  return tiles;
}

export async function prefetchMapTiles(
  south: number,
  west: number,
  north: number,
  east: number,
  zoomLevels = [12, 13, 14, 15],
): Promise<number> {
  if (!("caches" in window)) return 0;
  const cache = await caches.open("pgbot-map-tiles-v1");
  let count = 0;
  for (const z of zoomLevels) {
    const tiles = tileUrlsForBounds(south, west, north, east, z);
    await Promise.all(
      tiles.slice(0, 80).map(async (url) => {
        try {
          const res = await fetch(url, { mode: "cors" });
          if (res.ok) {
            await cache.put(url, res);
            count += 1;
          }
        } catch {
          /* ignore tile fetch errors */
        }
      }),
    );
  }
  return count;
}

function tileUrlsForBounds(
  south: number,
  west: number,
  north: number,
  east: number,
  zoom: number,
): string[] {
  const urls: string[] = [];
  const n = Math.pow(2, zoom);
  const xMin = lon2tile(west, zoom);
  const xMax = lon2tile(east, zoom);
  const yMin = lat2tile(north, zoom);
  const yMax = lat2tile(south, zoom);
  for (let x = xMin; x <= xMax; x++) {
    for (let y = yMin; y <= yMax; y++) {
      const cx = ((x % n) + n) % n;
      urls.push(`https://tile.openstreetmap.org/${zoom}/${cx}/${y}.png`);
    }
  }
  return urls;
}

function lon2tile(lon: number, zoom: number): number {
  return Math.floor(((lon + 180) / 360) * Math.pow(2, zoom));
}

function lat2tile(lat: number, zoom: number): number {
  const rad = (lat * Math.PI) / 180;
  return Math.floor(
    ((1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2) * Math.pow(2, zoom),
  );
}

/** Убираем старый SW с главной — он мешал загрузке на мобильных */
export async function clearStaleServiceWorkers(): Promise<void> {
  if (!("serviceWorker" in navigator)) return;
  const regs = await navigator.serviceWorker.getRegistrations();
  await Promise.all(regs.map((r) => r.unregister()));
  if ("caches" in window) {
    const keys = await caches.keys();
    await Promise.all(keys.filter((k) => k.startsWith("pgbot-")).map((k) => caches.delete(k)));
  }
}

export function registerServiceWorker(): void {
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {});
  }
}

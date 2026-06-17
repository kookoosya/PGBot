/** Parse ?source= URL param for public events API. */

const KNOWN_SOURCES = new Set([
  "vk",
  "pushkinland",
  "informpskov",
  "pln",
  "timepad",
  "kdc",
  "drampush",
  "kinopskov",
  "mirage",
  "silver",
  "orbilet",
  "proculture",
  "kudago",
  "manual",
]);

export function parseSourceParam(value: string | null): string | null {
  if (!value) return null;
  const normalized = value.trim().toLowerCase();
  if (!normalized || normalized.length > 32) return null;
  return KNOWN_SOURCES.has(normalized) ? normalized : null;
}

export function buildEventsSourceHref(source: string): string {
  return `/events?source=${encodeURIComponent(source)}`;
}

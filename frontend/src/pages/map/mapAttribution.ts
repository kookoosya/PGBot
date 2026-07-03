/** Leaflet prefix without the default Ukrainian flag SVG. */
export const LEAFLET_ATTRIBUTION_PREFIX =
  '<a href="https://leafletjs.com" title="JavaScript-библиотека интерактивных карт">Leaflet</a>';

export const LEAFLET_FLAG_MARKERS = [
  "leaflet-attribution-flag",
  "🇺🇦",
  "🇷🇺",
  "#4C7BE1",
  "#FFD500",
  "#E0BC00",
] as const;

type AttributionMap = {
  attributionControl: { setPrefix: (prefix: string) => void };
};

export function applyLeafletAttributionPrefix(map: AttributionMap) {
  map.attributionControl.setPrefix(LEAFLET_ATTRIBUTION_PREFIX);
}

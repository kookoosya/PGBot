import L from "leaflet";

import { CATEGORY_COLORS, CATEGORY_ICONS } from "./constants";

export function makeIcon(category: string, rating: number, isReference = false) {
  const color = CATEGORY_COLORS[category] || "#1a5c3a";
  const top = rating >= 4.5 ? " map-marker-top" : "";
  const ref = isReference ? " map-marker-ref" : "";
  const star = rating > 0 ? `<span class="map-marker-star">★${rating.toFixed(1)}</span>` : "";
  return L.divIcon({
    className: "",
    html: `<div class="map-marker-pin${top}${ref}" style="--pin-color:${color}"><span class="map-marker-emoji">${CATEGORY_ICONS[category] || "📍"}</span>${star}</div>`,
    iconSize: [38, 38],
    iconAnchor: [19, 19],
  });
}

export function makeRouteStopIcon(num: number) {
  return L.divIcon({
    className: "",
    html: `<div class="map-route-stop-pin">${num}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

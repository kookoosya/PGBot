import { useEffect, useRef } from "react";
import { useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";

import type { MapRoute, Place } from "@/lib/api/types/places";
import { makeIcon, makeRouteStopIcon } from "./icons";

export function MapSetCenter({ center }: { center: [number, number] | null }) {
  const map = useMap();
  const appliedRef = useRef(false);
  useEffect(() => {
    if (!center || appliedRef.current) return;
    map.setView(center, map.getZoom(), { animate: false });
    appliedRef.current = true;
  }, [center, map]);
  return null;
}

export function MapEvents({
  onBounds,
  pausedRef,
}: {
  onBounds: (b: { south: number; west: number; north: number; east: number }) => void;
  pausedRef: React.MutableRefObject<boolean>;
}) {
  const map = useMapEvents({
    moveend: () => {
      if (pausedRef.current) return;
      const b = map.getBounds();
      onBounds({ south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() });
    },
  });
  useEffect(() => {
    const b = map.getBounds();
    onBounds({ south: b.getSouth(), west: b.getWest(), north: b.getNorth(), east: b.getEast() });
  }, [map, onBounds]);
  return null;
}

export function ClusterLayer({
  places,
  onSelect,
}: {
  places: Place[];
  onSelect: (id: number) => void;
}) {
  const map = useMap();
  const clusterRef = useRef<L.MarkerClusterGroup | null>(null);

  useEffect(() => {
    if (!clusterRef.current) {
      clusterRef.current = L.markerClusterGroup({
        maxClusterRadius: 42,
        spiderfyOnMaxZoom: true,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        disableClusteringAtZoom: 17,
      });
      map.addLayer(clusterRef.current);
    }
    const group = clusterRef.current;
    group.clearLayers();
    places.forEach((p) => {
      const marker = L.marker([p.latitude, p.longitude], {
        icon: makeIcon(p.category, p.display_rating, false),
        zIndexOffset: Math.round(p.display_rating * 10),
      });
      const ratingLine = p.display_rating > 0
        ? `★ ${p.display_rating.toFixed(1)} (${p.display_review_count})`
        : "";
      marker.bindPopup(
        `<strong>${p.name}</strong><br/>${p.category_label}` +
        (p.address ? `<br/><span style="opacity:.8;font-size:12px">${p.address}</span>` : "") +
        (ratingLine ? `<br/>${ratingLine}` : "")
      );
      marker.on("click", () => onSelect(p.id));
      group.addLayer(marker);
    });
    return () => {
      group.clearLayers();
    };
  }, [places, map, onSelect]);

  return null;
}

export function RouteStopsLayer({ route }: { route: MapRoute | null }) {
  const map = useMap();

  useEffect(() => {
    if (!route) return;
    const markers: L.Marker[] = route.stops.map((stop, i) => {
      const marker = L.marker([stop.latitude, stop.longitude], {
        icon: makeRouteStopIcon(i + 1),
        zIndexOffset: 1000 + i,
      });
      marker.bindPopup(`<strong>${i + 1}. ${stop.name}</strong>${stop.address ? `<br/>${stop.address}` : ""}`);
      return marker;
    });
    markers.forEach((m) => m.addTo(map));
    return () => {
      markers.forEach((m) => map.removeLayer(m));
    };
  }, [route, map]);

  return null;
}

export function FlyToRoute({
  route,
  pausedRef,
}: {
  route: MapRoute | null;
  pausedRef: React.MutableRefObject<boolean>;
}) {
  const map = useMap();
  useEffect(() => {
    if (!route?.stops.length) return;
    pausedRef.current = true;
    const bounds = L.latLngBounds(route.stops.map((s) => [s.latitude, s.longitude] as [number, number]));
    map.fitBounds(bounds, { padding: [48, 48], maxZoom: 15, animate: true, duration: 0.5 });
    const t = window.setTimeout(() => {
      pausedRef.current = false;
    }, 700);
    return () => window.clearTimeout(t);
  }, [route, map, pausedRef]);
  return null;
}

export function FlyToPlace({
  place,
  pausedRef,
}: {
  place: Place | null;
  pausedRef: React.MutableRefObject<boolean>;
}) {
  const map = useMap();
  useEffect(() => {
    if (!place) return;
    pausedRef.current = true;
    const zoom = Math.max(map.getZoom(), 15);
    map.setView([place.latitude, place.longitude], zoom, { animate: true, duration: 0.4 });
    const t = window.setTimeout(() => {
      pausedRef.current = false;
    }, 600);
    return () => window.clearTimeout(t);
  }, [place, map, pausedRef]);
  return null;
}

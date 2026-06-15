import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { geoNavigateUrl, yandexMapsPointUrl, yandexRouteUrl } from "@/lib/pushkin";
import {
  cachePlacesForOffline,
  downloadOfflineMapPack,
  getOfflinePlaces,
  isOfflineMapReady,
  offlineBundleAge,
  registerServiceWorker,
} from "@/lib/offlineMap";
import { MapContainer, Polyline, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.markercluster";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { telHref } from "@/components/VkBotLink";
import { api, ComplaintType, MapFilterMode, MapRoute, MapStats, Place, PlaceDetail, TaxiService } from "@/lib/api";
import { MAP_TILE_OSM, MAP_TILE_SAT } from "@/lib/mapTiles";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

const CENTER: [number, number] = [57.0267, 28.91];

const FALLBACK_MAP_MODES: MapFilterMode[] = [
  { id: "shops", label: "🛒 Магазины", category: null, shops_only: true, useful_only: false, show_taxi: false },
  { id: "pharmacy", label: "💊 Аптеки", category: "pharmacy", shops_only: false, useful_only: false, show_taxi: false },
  { id: "taxi", label: "🚕 Такси", category: null, shops_only: false, useful_only: false, show_taxi: true },
  { id: "useful", label: "🏦 Полезное", category: null, shops_only: false, useful_only: true, show_taxi: false },
  { id: "landmarks", label: "🏛 Достопримечательности", category: "culture", shops_only: false, useful_only: false, show_taxi: false },
];

function formatPlaceNote(text: string | null | undefined): string | null {
  if (!text) return null;
  const cleaned = text
    .replace(/ · Данные из открытых источников — уточняйте перед визитом$/, "")
    .trim();
  return cleaned || null;
}

const CATEGORY_ICONS: Record<string, string> = {
  shop: "🛒", supermarket: "🏪", pharmacy: "💊", cafe: "☕",
  restaurant: "🍽", bank: "🏦", post: "📮", school: "🏫",
  hospital: "🏥", government: "🏛", transport: "🚌", culture: "🏛",
  hotel: "🏨", gas: "⛽", beauty: "💇", tyre: "🛞", auto: "🔧",
  taxi: "🚕", parking: "🅿️", other: "📍",
};

const CATEGORY_COLORS: Record<string, string> = {
  shop: "#e67e22", supermarket: "#d35400", pharmacy: "#27ae60",
  cafe: "#8e44ad", restaurant: "#c0392b", bank: "#2980b9",
  post: "#1abc9c", school: "#3498db", hospital: "#e74c3c",
  government: "#2c3e50", transport: "#16a085", culture: "#9b59b6",
  tyre: "#34495e", auto: "#7f8c8d", gas: "#f39c12", hotel: "#16a085",
  beauty: "#e91e63", parking: "#95a5a6", taxi: "#f1c40f",
  other: "#1a5c3a",
};

function makeIcon(category: string, rating: number, isReference = false) {
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

function makeRouteStopIcon(num: number) {
  return L.divIcon({
    className: "",
    html: `<div class="map-route-stop-pin">${num}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function formatSyncAge(iso: string | null): string {
  if (!iso) return "обновляется…";
  const diff = Date.now() - new Date(iso).getTime();
  const hours = Math.floor(diff / 3_600_000);
  if (hours < 1) return "только что";
  if (hours < 24) return `${hours} ч. назад`;
  return `${Math.floor(hours / 24)} дн. назад`;
}

function RatingBadge({ place }: { place: Place | PlaceDetail }) {
  if (place.display_rating <= 0) return <span className="org-rating-none">Нет оценок</span>;
  return (
    <div className="org-rating-badge">
      <span className="org-rating-score">★ {place.display_rating.toFixed(1)}</span>
      <span className="org-rating-meta">
        {place.display_review_count} отзывов
        {place.rating_source === "yandex" && " · Яндекс"}
        {place.rating_source === "reference" && " · справочник"}
        {place.rating_source === "users" && " · жители"}
      </span>
    </div>
  );
}

function MapEvents({
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

function ClusterLayer({
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
      const isRef = p.rating_source === "reference";
      const marker = L.marker([p.latitude, p.longitude], {
        icon: makeIcon(p.category, p.display_rating, isRef),
        zIndexOffset: (isRef ? 250 : 0) + Math.round(p.display_rating * 10),
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

function RouteStopsLayer({ route }: { route: MapRoute | null }) {
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

function FlyToPlace({
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

export function MapPage() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [selected, setSelected] = useState<PlaceDetail | null>(null);
  const [highlight, setHighlight] = useState<Place | null>(null);
  const [taxi, setTaxi] = useState<TaxiService[]>([]);
  const [category, setCategory] = useState("");
  const [shopsOnly, setShopsOnly] = useState(false);
  const [usefulOnly, setUsefulOnly] = useState(false);
  const [routes, setRoutes] = useState<MapRoute[]>([]);
  const [activeRoute, setActiveRoute] = useState<MapRoute | null>(null);
  const [mapReportTypes, setMapReportTypes] = useState<ComplaintType[]>([]);
  const [search, setSearch] = useState("");
  const [searchDebounced, setSearchDebounced] = useState("");
  const [mapStyle, setMapStyle] = useState<"scheme" | "satellite">("scheme");
  const [mapModes, setMapModes] = useState<MapFilterMode[]>(FALLBACK_MAP_MODES);
  const [taxiMode, setTaxiMode] = useState(false);
  const [complaintTypes, setComplaintTypes] = useState<ComplaintType[]>([]);
  const [tab, setTab] = useState<"info" | "review" | "complaint" | "report">("info");
  const [reviewForm, setReviewForm] = useState({ rating: 5, text: "", author_name: "" });
  const [complaintForm, setComplaintForm] = useState({
    complaint_type: "price_tag_fraud", description: "", price_tagged: "", price_charged: "", author_name: "",
  });
  const [reportForm, setReportForm] = useState({
    complaint_type: "map_wrong_hours", description: "", author_name: "",
  });
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState<"ok" | "err">("ok");
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [offlineReady, setOfflineReady] = useState(isOfflineMapReady());
  const [offlineBusy, setOfflineBusy] = useState(false);
  const [offlineMsg, setOfflineMsg] = useState("");
  const [mapStats, setMapStats] = useState<MapStats | null>(null);
  const [placesLoading, setPlacesLoading] = useState(true);
  const [placesError, setPlacesError] = useState(false);
  const [mobileTab, setMobileTab] = useState<"map" | "list">("map");
  const boundsRef = useRef<{ south: number; west: number; north: number; east: number } | null>(null);
  const boundsPausedRef = useRef(false);

  useEffect(() => {
    registerServiceWorker();
    api.getComplaintTypes().then(setComplaintTypes).catch(console.error);
    api.getMapReportTypes().then(setMapReportTypes).catch(console.error);
    api.getPlaceCategories().then(setCategories).catch(console.error);
    api.getTaxiServices().then(setTaxi).catch(console.error);
    api.getMapStats().then(setMapStats).catch(console.error);
    api.getMapFilterModes().then(setMapModes).catch(() => setMapModes(FALLBACK_MAP_MODES));
    api.getMapRoutes().then(setRoutes).catch(console.error);
  }, []);

  useEffect(() => {
    const t = window.setTimeout(() => setSearchDebounced(search.trim()), 400);
    return () => window.clearTimeout(t);
  }, [search]);

  const isLodging = category === "hotel";

  const activeFilterId = taxiMode
    ? "taxi"
    : shopsOnly
      ? "shops"
      : usefulOnly
        ? "useful"
        : mapModes.find((f) => f.category === category)?.id ?? "";

  const applyQuickFilter = (filter: MapFilterMode) => {
    const isActive = activeFilterId === filter.id;
    if (isActive) {
      setCategory("");
      setShopsOnly(false);
      setUsefulOnly(false);
      setTaxiMode(false);
      return;
    }
    setCategory(filter.category ?? "");
    setShopsOnly(Boolean(filter.shops_only));
    setUsefulOnly(Boolean(filter.useful_only));
    setTaxiMode(Boolean(filter.show_taxi));
  };

  const showRoute = (route: MapRoute) => {
    setActiveRoute(route);
    setSelected(null);
    setHighlight(null);
  };

  const loadPlaces = useCallback((bounds?: { south: number; west: number; north: number; east: number }) => {
    if (boundsPausedRef.current) return;
    if (taxiMode) {
      setPlaces([]);
      setPlacesLoading(false);
      setPlacesError(false);
      return;
    }
    if (bounds) boundsRef.current = bounds;
    const b = bounds || boundsRef.current;
    if (!b && !isLodging) return;
    const params: Record<string, string> = { page_size: "500", sort: "rating" };
    if (category) params.category = category;
    if (shopsOnly) params.shops_only = "true";
    if (usefulOnly) params.useful_only = "true";
    if (searchDebounced) params.search = searchDebounced;
    if (isLodging) {
      params.district = "true";
    } else if (b) {
      params.south = String(b.south);
      params.west = String(b.west);
      params.north = String(b.north);
      params.east = String(b.east);
    }
    setPlacesLoading(true);
    setPlacesError(false);
    api
      .getPlaces(params)
      .then((r) => {
        setPlaces(r.items);
        cachePlacesForOffline(r.items);
        setPlacesLoading(false);
      })
      .catch(() => {
        const cached = getOfflinePlaces();
        if (cached.length) {
          const filtered = category
            ? cached.filter((p) => p.category === category)
            : cached;
          setPlaces(filtered);
          setOfflineMsg("Нет сети — показаны сохранённые точки.");
          setPlacesLoading(false);
        } else {
          setPlaces([]);
          setPlacesError(true);
          setPlacesLoading(false);
        }
      });
  }, [category, shopsOnly, usefulOnly, searchDebounced, isLodging, taxiMode]);

  async function handleOfflineDownload() {
    setOfflineBusy(true);
    setOfflineMsg("");
    try {
      const all = await api.getPlaces({ district: "true", page_size: "500", sort: "rating" });
      const n = await downloadOfflineMapPack(all.items);
      setOfflineReady(true);
      const age = offlineBundleAge();
      setOfflineMsg(`Офлайн готов: ${all.items.length} точек, ${n} тайлов карты${age ? ` · ${new Date(age).toLocaleString("ru")}` : ""}.`);
    } catch {
      setOfflineMsg("Не удалось скачать. Проверьте интернет.");
    } finally {
      setOfflineBusy(false);
    }
  }

  useEffect(() => {
    if (boundsRef.current || isLodging) loadPlaces(boundsRef.current ?? undefined);
  }, [category, shopsOnly, usefulOnly, searchDebounced, loadPlaces, isLodging]);

  const sortedPlaces = useMemo(
    () => [...places].sort((a, b) => {
      const refA = a.rating_source === "reference" ? 1 : 0;
      const refB = b.rating_source === "reference" ? 1 : 0;
      if (refB !== refA) return refB - refA;
      return b.display_rating - a.display_rating || b.display_review_count - a.display_review_count || a.name.localeCompare(b.name, "ru");
    }),
    [places]
  );

  const openPlace = async (id: number) => {
    boundsPausedRef.current = true;
    try {
      const detail = await api.getPlace(id);
      setSelected(detail);
      setHighlight(detail);
      setTab("info");
      setMsg("");
      setMsgType("ok");
    } catch {
      setMsg("Не удалось загрузить организацию. Попробуйте ещё раз.");
      setMsgType("err");
    } finally {
      window.setTimeout(() => {
        boundsPausedRef.current = false;
      }, 800);
    }
  };

  const submitReview = async () => {
    if (!selected) return;
    try {
      await api.addReview(selected.id, reviewForm);
      setMsg("Отзыв добавлен!");
      setMsgType("ok");
      openPlace(selected.id);
      loadPlaces();
      setTab("info");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Не удалось отправить отзыв");
      setMsgType("err");
    }
  };

  const submitComplaint = async () => {
    if (!selected || complaintForm.description.length < 10) return;
    try {
      await api.addComplaint(selected.id, complaintForm);
      setMsg("Жалоба принята!");
      setMsgType("ok");
      openPlace(selected.id);
      setTab("info");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Не удалось отправить жалобу");
      setMsgType("err");
    }
  };

  const submitReport = async () => {
    if (!selected || reportForm.description.length < 10) return;
    try {
      await api.addComplaint(selected.id, reportForm);
      setMsg("Спасибо! Проверим и обновим карту.");
      setMsgType("ok");
      setReportForm({ complaint_type: "map_wrong_hours", description: "", author_name: "" });
      setTab("info");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Не удалось отправить сообщение");
      setMsgType("err");
    }
  };

  return (
    <div>
      <div className="page-section pb-2">
        <PageHeader
          icon="🗺"
          title="Карта посёлка"
          subtitle={PUSHKIN_QUOTES.map}
        />
      </div>


      {routes.length > 0 && (
        <div className="page-section pb-3">
          <div className="map-routes-panel">
            <h3 className="map-routes-title">🧭 Маршруты для туристов</h3>
            <div className="map-routes-grid">
              {routes.map((route) => (
                <button
                  key={route.id}
                  type="button"
                  className={`map-route-card${activeRoute?.id === route.id ? " map-route-card-active" : ""}`}
                  onClick={() => showRoute(route)}
                >
                  <strong>{route.title}</strong>
                  <span className="text-xs opacity-80">{route.duration}</span>
                  <p className="text-xs m-0 mt-1">{route.description}</p>
                </button>
              ))}
            </div>
            {activeRoute && (
              <div className="map-route-detail">
                <div className="flex items-center justify-between gap-2 mt-3">
                  <h4 className="m-0 text-sm font-bold">{activeRoute.title}</h4>
                  <button type="button" className="text-xs opacity-70" onClick={() => setActiveRoute(null)}>
                    Скрыть
                  </button>
                </div>
                <p className="text-xs text-muted-foreground m-0 mt-1">{activeRoute.duration} · {activeRoute.description}</p>
                <ol className="map-route-stops">
                  {activeRoute.stops.map((stop, i) => (
                    <li key={`${stop.name}-${i}`} className="map-route-stop">
                      <span className="map-route-stop-num">{i + 1}</span>
                      <div>
                        <strong className="text-sm">{stop.name}</strong>
                        {stop.address && <p className="text-xs text-muted-foreground m-0">{stop.address}</p>}
                        <div className="map-route-stop-links">
                          <a href={yandexMapsPointUrl(stop.latitude, stop.longitude, stop.name)} target="_blank" rel="noopener noreferrer" className="text-xs">
                            Яндекс.Карты
                          </a>
                          <a href={yandexRouteUrl(stop.latitude, stop.longitude)} target="_blank" rel="noopener noreferrer" className="text-xs">
                            Маршрут
                          </a>
                          <a href={geoNavigateUrl(stop.latitude, stop.longitude)} className="text-xs">
                            GPS
                          </a>
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>
      )}

      {taxi.length > 0 && (
        <div className="page-section pb-3">
          <div className={`taxi-panel${taxiMode ? " taxi-panel-active" : ""}`}>
            <div className="taxi-panel-header">
              <h3>🚕 Такси {taxiMode ? "в посёлке" : "для туристов"}</h3>
            </div>
            <div className="taxi-grid">
              {taxi.map((t) => (
                <a
                  key={t.id}
                  href={telHref(t.phone)}
                  className="taxi-card"
                >
                  <div className="taxi-card-top">
                    <strong>{t.name}</strong>
                    {t.is_24h && <span className="taxi-24h">24/7</span>}
                  </div>
                  <p className="taxi-phone">{t.phone}</p>
                  {t.phones_extra && <p className="taxi-phone-extra">{t.phones_extra}</p>}
                  <p className="taxi-desc">{t.description}</p>
                  <div className="taxi-meta">
                    {t.rating > 0 && <span>★ {t.rating}</span>}
                    {t.price_from != null && <span>от {t.price_from} ₽</span>}
                  </div>
                </a>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="map-mobile-tabs lg:hidden page-section pb-2">
        <button
          type="button"
          className={`map-mobile-tab ${mobileTab === "map" ? "map-mobile-tab-active" : ""}`}
          onClick={() => setMobileTab("map")}
        >
          🗺 Карта
        </button>
        <button
          type="button"
          className={`map-mobile-tab ${mobileTab === "list" ? "map-mobile-tab-active" : ""}`}
          onClick={() => setMobileTab("list")}
        >
          📋 Список ({sortedPlaces.length})
        </button>
      </div>

      <div className="flex flex-col lg:flex-row map-layout">
        <div className={`map-pane flex-1 relative ${mobileTab === "list" ? "map-pane-hidden-mobile" : ""}`}>
          <MapContainer center={CENTER} zoom={14} className="map-canvas z-0" scrollWheelZoom>
            <TileLayer
              attribution={mapStyle === "scheme"
                ? "© OpenStreetMap · справочник посёлка"
                : "© Esri"}
              url={mapStyle === "scheme" ? MAP_TILE_OSM : MAP_TILE_SAT}
            />
            <MapEvents onBounds={loadPlaces} pausedRef={boundsPausedRef} />
            <ClusterLayer places={sortedPlaces} onSelect={openPlace} />
            {activeRoute && activeRoute.stops.length > 1 && (
              <>
                <Polyline
                  positions={activeRoute.stops.map((s) => [s.latitude, s.longitude] as [number, number])}
                  pathOptions={{ color: "#c9a227", weight: 4, opacity: 0.85, dashArray: "10 8" }}
                />
                <RouteStopsLayer route={activeRoute} />
              </>
            )}
            <FlyToPlace place={highlight} pausedRef={boundsPausedRef} />
          </MapContainer>

          {taxiMode && (
            <div className="map-taxi-overlay" aria-hidden>
              <p>🚕 Режим такси — выберите службу выше</p>
            </div>
          )}

          <div className="map-overlay-controls">
            <button type="button" className={`map-layer-btn ${mapStyle === "scheme" ? "active" : ""}`} onClick={() => setMapStyle("scheme")}>
              Схема
            </button>
            <button type="button" className={`map-layer-btn ${mapStyle === "satellite" ? "active" : ""}`} onClick={() => setMapStyle("satellite")}>
              Спутник
            </button>
          </div>

          {mapStats && (
            <div className="map-stats-overlay">
              <p className="font-bold m-0 text-sm">📍 {mapStats.total_places} мест</p>
              <p className="text-xs text-muted-foreground m-0 mt-1">
                {formatSyncAge(mapStats.last_sync)}
              </p>
            </div>
          )}

        </div>

        <div className={`w-full lg:w-[420px] border-l map-sidebar map-sidebar-glass overflow-y-auto ${mobileTab === "map" ? "map-sidebar-hidden-mobile" : ""}`}>
          <div className="p-4 space-y-3 border-b sticky top-0 map-sidebar-head z-10">
            <input
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="Поиск организации..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <div className="map-filter-scroll">
              {mapModes.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className={`map-filter-chip${activeFilterId === f.id ? " map-filter-chip-active" : ""}`}
                  onClick={() => applyQuickFilter(f)}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <div className="map-filter-row">
              <select
                className="text-sm rounded-md border px-2 py-1.5 flex-1"
                value={shopsOnly ? "" : category}
                onChange={(e) => {
                  setShopsOnly(false);
                  setUsefulOnly(false);
                  setCategory(e.target.value);
                }}
              >
                <option value="">Все категории</option>
                {categories.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
              <button
                type="button"
                className="map-offline-btn"
                onClick={handleOfflineDownload}
                disabled={offlineBusy}
                title="Скачать карту для офлайн"
              >
                {offlineBusy ? "…" : offlineReady ? "📥" : "📥 Офлайн"}
              </button>
            </div>
            {offlineMsg ? <p className="text-xs text-muted-foreground">{offlineMsg}</p> : null}
          </div>

          {selected ? (
            <div className="p-4 org-detail-card">
              <button className="text-sm text-muted-foreground mb-3" onClick={() => { setSelected(null); setHighlight(null); }}>← К списку</button>

              <div className="org-detail-header">
                <span className="org-detail-icon">{CATEGORY_ICONS[selected.category] || "📍"}</span>
                <div>
                  <h3 className="text-xl font-bold leading-tight">{selected.name}</h3>
                  <p className="text-sm text-muted-foreground">{selected.category_label}</p>
                </div>
              </div>

              <RatingBadge place={selected} />

              {selected.address && (
                <p className="org-detail-row">📍 {selected.address}</p>
              )}
              {selected.opening_hours && (
                <div className="org-hours-box">
                  <p className="font-medium">🕐 {selected.opening_hours}</p>
                </div>
              )}
              {selected.phone && (
                <p className="org-detail-row">
                  📞 <a href={`tel:${selected.phone.replace(/\s/g, "")}`} className="clickable-phone">{selected.phone}</a>
                </p>
              )}
              {selected.website && (
                <p className="org-detail-row">
                  🔗{" "}
                  <a href={selected.website} target="_blank" rel="noopener noreferrer">
                    Сайт
                  </a>
                </p>
              )}
              {formatPlaceNote(selected.description) && (
                <p className="text-sm text-muted-foreground mt-2">{formatPlaceNote(selected.description)}</p>
              )}
              <p className="text-xs text-muted-foreground mt-2 m-0">
                Данные из открытых источников — уточняйте часы и телефон перед визитом.
              </p>

              <div className="org-action-grid mt-4">
                {selected.phone && (
                  <a href={`tel:${selected.phone.replace(/\s/g, "")}`} className="org-action-btn org-action-call no-underline">
                    📞 Позвонить
                  </a>
                )}
                <a
                  href={yandexRouteUrl(selected.latitude, selected.longitude)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="org-action-btn org-action-route no-underline"
                >
                  🧭 Маршрут
                </a>
                <a
                  href={selected.yandex_url || yandexMapsPointUrl(selected.latitude, selected.longitude, selected.name)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="org-action-btn org-action-maps no-underline"
                >
                  🗺 На карте
                </a>
                <a
                  href={geoNavigateUrl(selected.latitude, selected.longitude)}
                  className="org-action-btn org-action-offline no-underline"
                >
                  📍 GPS
                </a>
              </div>

              <div className="org-tabs mt-4">
                {(["info", "review", "report", "complaint"] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    className={`org-tab${tab === t ? " org-tab-active" : ""}`}
                    onClick={() => setTab(t)}
                  >
                    {t === "info" ? "Отзывы" : t === "review" ? "Оценить" : t === "report" ? "Ошибка" : "Жалоба"}
                  </button>
                ))}
              </div>

              {msg && (
                <p className={`text-sm mt-2 ${msgType === "ok" ? "text-green-700" : "text-destructive"}`}>
                  {msg}
                </p>
              )}

              {tab === "info" && (
                <div className="mt-3 space-y-2">
                  {selected.reviews.length === 0 && <p className="text-sm text-muted-foreground">Отзывов жителей пока нет — оцените первым!</p>}
                  {selected.reviews.map((r) => (
                    <div key={r.id} className="org-review-card">
                      <span>{"★".repeat(r.rating)}</span> <strong>{r.author_name}</strong>
                      <p>{r.text}</p>
                    </div>
                  ))}
                </div>
              )}

              {tab === "review" && (
                <div className="mt-3 space-y-3">
                  <select className="w-full border rounded px-2 py-1" value={reviewForm.rating} onChange={(e) => setReviewForm({ ...reviewForm, rating: +e.target.value })}>
                    {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{"★".repeat(n)}</option>)}
                  </select>
                  <textarea className="w-full border rounded p-2 text-sm min-h-[80px]" placeholder="Ваш отзыв..." value={reviewForm.text} onChange={(e) => setReviewForm({ ...reviewForm, text: e.target.value })} />
                  <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Ваше имя" value={reviewForm.author_name} onChange={(e) => setReviewForm({ ...reviewForm, author_name: e.target.value })} />
                  <Button className="w-full" onClick={submitReview}>Отправить отзыв</Button>
                </div>
              )}

              {tab === "report" && (
                <div className="mt-3 space-y-3">
                  <p className="text-xs text-muted-foreground m-0">Заведение закрылось? Неверный телефон? Напишите — обновим карту.</p>
                  <select className="w-full border rounded px-2 py-1 text-sm" value={reportForm.complaint_type} onChange={(e) => setReportForm({ ...reportForm, complaint_type: e.target.value })}>
                    {mapReportTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <textarea className="w-full border rounded p-2 text-sm min-h-[80px]" placeholder="Что не так? Например: закрыто, другой телефон..." value={reportForm.description} onChange={(e) => setReportForm({ ...reportForm, description: e.target.value })} />
                  <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Ваше имя (необязательно)" value={reportForm.author_name} onChange={(e) => setReportForm({ ...reportForm, author_name: e.target.value })} />
                  <Button className="w-full" disabled={reportForm.description.length < 10} onClick={submitReport}>
                    Отправить
                  </Button>
                </div>
              )}

              {tab === "complaint" && (
                <div className="mt-3 space-y-3">
                  <p className="text-xs text-muted-foreground m-0">Жалоба на магазин: цена, чек, товар.</p>
                  <select className="w-full border rounded px-2 py-1 text-sm" value={complaintForm.complaint_type} onChange={(e) => setComplaintForm({ ...complaintForm, complaint_type: e.target.value })}>
                    {complaintTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <div className="grid grid-cols-2 gap-2">
                    <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Цена на ценнике" value={complaintForm.price_tagged} onChange={(e) => setComplaintForm({ ...complaintForm, price_tagged: e.target.value })} />
                    <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Взяли с вас" value={complaintForm.price_charged} onChange={(e) => setComplaintForm({ ...complaintForm, price_charged: e.target.value })} />
                  </div>
                  <textarea className="w-full border rounded p-2 text-sm min-h-[100px]" placeholder="Опишите ситуацию (мин. 10 символов)..." value={complaintForm.description} onChange={(e) => setComplaintForm({ ...complaintForm, description: e.target.value })} />
                  <Button className="w-full" variant="destructive" disabled={complaintForm.description.length < 10} onClick={submitComplaint}>
                    Подать жалобу
                  </Button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-3 space-y-2">
              <p className="text-xs text-muted-foreground px-1">
                {placesLoading
                  ? "Загрузка…"
                  : placesError
                    ? "Ошибка загрузки"
                    : `${sortedPlaces.length} на карте`}
              </p>
              {sortedPlaces.map((p) => (
                <button key={p.id} className="org-list-card" onClick={() => { openPlace(p.id); setMobileTab("map"); }}>
                  <span className="org-list-icon">{CATEGORY_ICONS[p.category] || "📍"}</span>
                  <div className="org-list-body">
                    <div className="flex justify-between gap-2 items-start">
                      <strong className="text-sm text-left">{p.name}</strong>
                      <div className="flex items-center gap-1 shrink-0">
                        {p.rating_source === "reference" && (
                          <span className="org-list-ref" title="Проверенный справочник">✓</span>
                        )}
                        {p.display_rating > 0 && (
                          <span className="org-list-rating">★ {p.display_rating.toFixed(1)}</span>
                        )}
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground text-left">{p.category_label} · {p.address || "Пушкинские Горы"}</p>
                    {p.phone && <p className="text-xs mt-1 text-left">📞 {p.phone}</p>}
                  </div>
                </button>
              ))}
              {!placesLoading && placesError && (
                <div className="text-center py-8 px-3">
                  <p className="text-muted-foreground mb-3">Не удалось загрузить справочник</p>
                  <Button size="sm" variant="outline" onClick={() => loadPlaces(boundsRef.current ?? undefined)}>
                    Повторить
                  </Button>
                </div>
              )}
              {!placesLoading && !placesError && sortedPlaces.length === 0 && (
                <p className="text-center text-muted-foreground py-8">Ничего не найдено. Смените фильтр или поиск.</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

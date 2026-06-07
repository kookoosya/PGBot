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
import { MapContainer, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.markercluster";
import { Button } from "@/components/ui/button";
import { telHref } from "@/components/VkBotLink";
import { api, Place, PlaceDetail, ComplaintType, TaxiService } from "@/lib/api";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

const CENTER: [number, number] = [57.0267, 28.91];

const CATEGORY_ICONS: Record<string, string> = {
  shop: "🛒", supermarket: "🏪", pharmacy: "💊", cafe: "☕",
  restaurant: "🍽", bank: "🏦", post: "📮", school: "🏫",
  hospital: "🏥", government: "🏛", transport: "🚌", culture: "🎭",
  hotel: "🏨", rental: "🏠", gas: "⛽", beauty: "💇", tyre: "🛞", auto: "🔧",
  taxi: "🚕", other: "📍",
};

const CATEGORY_COLORS: Record<string, string> = {
  shop: "#e67e22", supermarket: "#d35400", pharmacy: "#27ae60",
  cafe: "#8e44ad", restaurant: "#c0392b", bank: "#2980b9",
  government: "#2c3e50", culture: "#9b59b6", tyre: "#34495e",
  auto: "#7f8c8d", gas: "#f39c12", hotel: "#16a085", rental: "#db2777", beauty: "#e91e63",
  other: "#1a5c3a",
};

const OSM_TILES = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const SAT_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}";

function makeIcon(category: string, rating: number) {
  const color = CATEGORY_COLORS[category] || "#1a5c3a";
  const star = rating > 0 ? `<span style="font-size:8px;color:#ffd700">★${rating.toFixed(1)}</span>` : "";
  return L.divIcon({
    className: "",
    html: `<div class="map-marker-pin" style="background:${color}">${CATEGORY_ICONS[category] || "📍"}${star}</div>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
  });
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
        maxClusterRadius: 45,
        spiderfyOnMaxZoom: false,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: false,
      });
      map.addLayer(clusterRef.current);
    }
    const group = clusterRef.current;
    group.clearLayers();
    places.forEach((p) => {
      const marker = L.marker([p.latitude, p.longitude], {
        icon: makeIcon(p.category, p.display_rating),
      });
      marker.bindPopup(
        `<strong>${p.name}</strong><br/>${p.category_label}<br/>` +
        (p.display_rating > 0 ? `★ ${p.display_rating} (${p.display_review_count})` : "")
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
  const [search, setSearch] = useState("");
  const [mapStyle, setMapStyle] = useState<"scheme" | "satellite">("scheme");
  const [showTaxi, setShowTaxi] = useState(true);
  const [complaintTypes, setComplaintTypes] = useState<ComplaintType[]>([]);
  const [tab, setTab] = useState<"info" | "review" | "complaint">("info");
  const [reviewForm, setReviewForm] = useState({ rating: 5, text: "", author_name: "" });
  const [complaintForm, setComplaintForm] = useState({
    complaint_type: "price_tag_fraud", description: "", price_tagged: "", price_charged: "", author_name: "",
  });
  const [msg, setMsg] = useState("");
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [offlineReady, setOfflineReady] = useState(isOfflineMapReady());
  const [offlineBusy, setOfflineBusy] = useState(false);
  const [offlineMsg, setOfflineMsg] = useState("");
  const boundsRef = useRef<{ south: number; west: number; north: number; east: number } | null>(null);
  const boundsPausedRef = useRef(false);

  useEffect(() => {
    registerServiceWorker();
    api.getComplaintTypes().then(setComplaintTypes).catch(console.error);
    api.getPlaceCategories().then(setCategories).catch(console.error);
    api.getTaxiServices().then(setTaxi).catch(console.error);
  }, []);

  const isLodging = category === "hotel" || category === "rental";

  const loadPlaces = useCallback((bounds?: { south: number; west: number; north: number; east: number }) => {
    if (boundsPausedRef.current) return;
    if (bounds) boundsRef.current = bounds;
    const b = bounds || boundsRef.current;
    if (!b && !isLodging) return;
    const params: Record<string, string> = { page_size: "500", sort: "rating" };
    if (category) params.category = category;
    if (shopsOnly) params.shops_only = "true";
    if (search) params.search = search;
    if (isLodging) {
      params.district = "true";
    } else if (b) {
      params.south = String(b.south);
      params.west = String(b.west);
      params.north = String(b.north);
      params.east = String(b.east);
    }
    api
      .getPlaces(params)
      .then((r) => {
        setPlaces(r.items);
        cachePlacesForOffline(r.items);
      })
      .catch(() => {
        const cached = getOfflinePlaces();
        if (cached.length) {
          const filtered = category
            ? cached.filter((p) => p.category === category)
            : cached;
          setPlaces(filtered);
          setOfflineMsg("Нет сети — показаны сохранённые точки.");
        }
      });
  }, [category, shopsOnly, search, isLodging]);

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
  }, [category, shopsOnly, search, loadPlaces, isLodging]);

  const sortedPlaces = useMemo(
    () => [...places].sort((a, b) => b.display_rating - a.display_rating || b.display_review_count - a.display_review_count),
    [places]
  );

  const openPlace = async (id: number) => {
    boundsPausedRef.current = true;
    const detail = await api.getPlace(id);
    setSelected(detail);
    setHighlight(detail);
    setTab("info");
    setMsg("");
    window.setTimeout(() => {
      boundsPausedRef.current = false;
    }, 800);
  };

  const submitReview = async () => {
    if (!selected) return;
    await api.addReview(selected.id, reviewForm);
    setMsg("Отзыв добавлен!");
    openPlace(selected.id);
    loadPlaces();
    setTab("info");
  };

  const submitComplaint = async () => {
    if (!selected || complaintForm.description.length < 10) return;
    await api.addComplaint(selected.id, complaintForm);
    setMsg("Жалоба принята!");
    openPlace(selected.id);
    setTab("info");
  };

  return (
    <div>
      <div className="page-section pb-2">
        <div className="page-header mb-0">
          <div className="page-header-inner">
            <span className="page-header-icon">🗺</span>
            <div>
              <h1 className="page-header-title">Карта посёлка</h1>
              <p className="page-header-subtitle">{PUSHKIN_QUOTES.map}</p>
            </div>
          </div>
        </div>
      </div>


      {showTaxi && taxi.length > 0 && (
        <div className="page-section pb-3">
          <div className="taxi-panel">
            <div className="taxi-panel-header">
              <h3>🚕 Такси для туристов</h3>
              <button type="button" className="text-xs opacity-60" onClick={() => setShowTaxi(false)}>скрыть</button>
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

      <div className="flex flex-col lg:flex-row map-layout">
        <div className="map-pane flex-1 relative">
          <MapContainer center={CENTER} zoom={14} className="map-canvas z-0" scrollWheelZoom>
            <TileLayer
              attribution={mapStyle === "scheme"
                ? '&copy; <a href="https://www.openstreetmap.org/">OSM</a> · данные Яндекс/справочник'
                : '&copy; Esri'}
              url={mapStyle === "scheme" ? OSM_TILES : SAT_TILES}
            />
            <MapEvents onBounds={loadPlaces} pausedRef={boundsPausedRef} />
            <ClusterLayer places={places} onSelect={openPlace} />
            <FlyToPlace place={highlight} pausedRef={boundsPausedRef} />
          </MapContainer>

          <div className="map-overlay-controls">
            <button type="button" className={`map-layer-btn ${mapStyle === "scheme" ? "active" : ""}`} onClick={() => setMapStyle("scheme")}>
              Схема
            </button>
            <button type="button" className={`map-layer-btn ${mapStyle === "satellite" ? "active" : ""}`} onClick={() => setMapStyle("satellite")}>
              Спутник
            </button>
          </div>

        </div>

        <div className="w-full lg:w-[420px] border-l bg-card overflow-y-auto map-sidebar">
          <div className="p-4 space-y-3 border-b sticky top-0 bg-card z-10">
            <input
              className="w-full rounded-md border px-3 py-2 text-sm"
              placeholder="Поиск организации..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && loadPlaces()}
            />
            <div className="flex gap-2 flex-wrap">
              <Button size="sm" variant={shopsOnly ? "default" : "outline"} onClick={() => setShopsOnly(!shopsOnly)}>
                🛒 Магазины
              </Button>
              <Button size="sm" variant={category === "pharmacy" ? "default" : "outline"} onClick={() => setCategory(category === "pharmacy" ? "" : "pharmacy")}>
                💊 Аптеки
              </Button>
              <Button size="sm" variant={category === "tyre" ? "default" : "outline"} onClick={() => setCategory(category === "tyre" ? "" : "tyre")}>
                🛞 Шины
              </Button>
              <Button size="sm" variant={category === "hotel" ? "default" : "outline"} onClick={() => setCategory(category === "hotel" ? "" : "hotel")}>
                🏨 Гостиницы
              </Button>
              <Button size="sm" variant={category === "rental" ? "default" : "outline"} onClick={() => setCategory(category === "rental" ? "" : "rental")}>
                🏠 Посуточно
              </Button>
              <Button size="sm" variant={offlineReady ? "outline" : "default"} onClick={handleOfflineDownload} disabled={offlineBusy}>
                {offlineBusy ? "Скачиваю…" : offlineReady ? "📥 Обновить офлайн" : "📥 Офлайн"}
              </Button>
              <select className="text-sm rounded-md border px-2 py-1 flex-1 min-w-[120px]" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="">Все</option>
                {categories.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
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
                    {selected.category === "rental" ? "Объявление / бронь" : "Сайт"}
                  </a>
                </p>
              )}
              {selected.description && (
                <p className="text-sm text-muted-foreground mt-2">{selected.description}</p>
              )}

              <div className="flex flex-wrap gap-2 mt-4">
                <a
                  href={yandexRouteUrl(selected.latitude, selected.longitude)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-hero-primary text-xs px-3 py-2 no-underline"
                >
                  🧭 Проложить маршрут
                </a>
                <a
                  href={geoNavigateUrl(selected.latitude, selected.longitude)}
                  className="btn-hero-secondary text-xs px-3 py-2 no-underline"
                >
                  📍 Навигатор офлайн
                </a>
                <a
                  href={selected.yandex_url || yandexMapsPointUrl(selected.latitude, selected.longitude, selected.name)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-hero-secondary text-xs px-3 py-2 no-underline"
                >
                  Яндекс.Карты
                </a>
              </div>

              <div className="flex gap-1 mt-4 border-b">
                {(["info", "review", "complaint"] as const).map((t) => (
                  <button key={t} className={`px-3 py-2 text-sm ${tab === t ? "border-b-2 border-amber-500 font-medium" : "text-muted-foreground"}`} onClick={() => setTab(t)}>
                    {t === "info" ? "Отзывы" : t === "review" ? "Оценить" : "Жалоба"}
                  </button>
                ))}
              </div>

              {msg && <p className="text-sm text-green-700 mt-2">{msg}</p>}

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

              {tab === "complaint" && (
                <div className="mt-3 space-y-3">
                  <select className="w-full border rounded px-2 py-1 text-sm" value={complaintForm.complaint_type} onChange={(e) => setComplaintForm({ ...complaintForm, complaint_type: e.target.value })}>
                    {complaintTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                  <textarea className="w-full border rounded p-2 text-sm min-h-[100px]" placeholder="Опишите ситуацию..." value={complaintForm.description} onChange={(e) => setComplaintForm({ ...complaintForm, description: e.target.value })} />
                  <Button className="w-full" variant="destructive" onClick={submitComplaint}>Подать жалобу</Button>
                </div>
              )}
            </div>
          ) : (
            <div className="p-3 space-y-2">
              <p className="text-xs text-muted-foreground px-1">По рейтингу · клик — карточка и переход на карте</p>
              {sortedPlaces.map((p) => (
                <button key={p.id} className="org-list-card" onClick={() => openPlace(p.id)}>
                  <span className="org-list-icon">{CATEGORY_ICONS[p.category] || "📍"}</span>
                  <div className="org-list-body">
                    <div className="flex justify-between gap-2">
                      <strong className="text-sm">{p.name}</strong>
                      {p.display_rating > 0 && (
                        <span className="org-list-rating">★ {p.display_rating.toFixed(1)}</span>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground">{p.category_label} · {p.address || "Пушкинские Горы"}</p>
                    {p.phone && <p className="text-xs mt-1">📞 {p.phone}</p>}
                  </div>
                </button>
              ))}
              {sortedPlaces.length === 0 && (
                <p className="text-center text-muted-foreground py-8">Загрузка организаций...</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

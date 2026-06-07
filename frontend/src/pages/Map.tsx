import { useCallback, useEffect, useState } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Button } from "@/components/ui/button";
import { api, Place, PlaceDetail, ComplaintType } from "@/lib/api";

const CENTER: [number, number] = [57.0267, 28.91];

const CATEGORY_ICONS: Record<string, string> = {
  shop: "🛒", supermarket: "🏪", pharmacy: "💊", cafe: "☕",
  restaurant: "🍽", bank: "🏦", post: "📮", school: "🏫",
  hospital: "🏥", government: "🏛", transport: "🚌", culture: "🎭",
  hotel: "🏨", gas: "⛽", other: "📍",
};

const CATEGORY_COLORS: Record<string, string> = {
  shop: "#e67e22", supermarket: "#d35400", pharmacy: "#27ae60",
  cafe: "#8e44ad", restaurant: "#c0392b", bank: "#2980b9",
  government: "#2c3e50", culture: "#9b59b6", other: "#7f8c8d",
};

function makeIcon(category: string) {
  const color = CATEGORY_COLORS[category] || "#1a5c3a";
  return L.divIcon({
    className: "",
    html: `<div style="background:${color};width:28px;height:28px;border-radius:50%;border:2px solid #c9a227;display:flex;align-items:center;justify-content:center;font-size:14px;box-shadow:0 2px 6px rgba(0,0,0,.3)">${CATEGORY_ICONS[category] || "📍"}</div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 14],
  });
}

function MapEvents({ onBounds }: { onBounds: (b: { south: number; west: number; north: number; east: number }) => void }) {
  const map = useMapEvents({
    moveend: () => {
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

export function MapPage() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [selected, setSelected] = useState<PlaceDetail | null>(null);
  const [stats, setStats] = useState<{ total_places: number; by_category: Record<string, number> } | null>(null);
  const [category, setCategory] = useState("");
  const [shopsOnly, setShopsOnly] = useState(false);
  const [search, setSearch] = useState("");
  const [complaintTypes, setComplaintTypes] = useState<ComplaintType[]>([]);
  const [tab, setTab] = useState<"info" | "review" | "complaint">("info");
  const [reviewForm, setReviewForm] = useState({ rating: 5, text: "", author_name: "" });
  const [complaintForm, setComplaintForm] = useState({
    complaint_type: "price_tag_fraud", description: "", price_tagged: "", price_charged: "", author_name: "",
  });
  const [msg, setMsg] = useState("");

  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);

  useEffect(() => {
    api.getMapStats().then(setStats).catch(console.error);
    api.getComplaintTypes().then(setComplaintTypes).catch(console.error);
    api.getPlaceCategories().then(setCategories).catch(console.error);
  }, []);

  const loadPlaces = useCallback((bounds?: { south: number; west: number; north: number; east: number }) => {
    const params: Record<string, string> = { page_size: "500" };
    if (category) params.category = category;
    if (shopsOnly) params.shops_only = "true";
    if (search) params.search = search;
    if (bounds) {
      params.south = String(bounds.south);
      params.west = String(bounds.west);
      params.north = String(bounds.north);
      params.east = String(bounds.east);
    }
    api.getPlaces(params).then((r) => setPlaces(r.items)).catch(console.error);
  }, [category, shopsOnly, search]);

  const openPlace = async (id: number) => {
    const detail = await api.getPlace(id);
    setSelected(detail);
    setTab("info");
    setMsg("");
  };

  const submitReview = async () => {
    if (!selected) return;
    await api.addReview(selected.id, reviewForm);
    setMsg("Отзыв добавлен!");
    openPlace(selected.id);
    setTab("info");
  };

  const submitComplaint = async () => {
    if (!selected || complaintForm.description.length < 10) return;
    await api.addComplaint(selected.id, complaintForm);
    setMsg("Жалоба принята и передана в народный контроль!");
    openPlace(selected.id);
    setTab("info");
  };

  return (
    <div>
      <div className="page-section pb-4">
        <div className="page-header mb-0">
          <div className="page-header-inner">
            <span className="page-header-icon">🗺</span>
            <div>
              <h1 className="page-header-title">Карта посёлка</h1>
              <p className="page-header-subtitle">Магазины, аптеки, службы — отзывы и жалобы жителей</p>
            </div>
          </div>
        </div>
      </div>
    <div className="flex flex-col lg:flex-row map-layout">
      <div className="flex-1 relative min-h-[400px]">
        <MapContainer center={CENTER} zoom={14} className="h-full w-full z-0">
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapEvents onBounds={loadPlaces} />
          {places.map((p) => (
            <Marker key={p.id} position={[p.latitude, p.longitude]} icon={makeIcon(p.category)} eventHandlers={{ click: () => openPlace(p.id) }}>
              <Popup>
                <strong>{p.name}</strong><br />
                {p.category_label}<br />
                {p.avg_rating > 0 && <span>⭐ {p.avg_rating} ({p.review_count})</span>}
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        <div className="absolute top-3 left-3 z-[1000] pushkin-card p-3 text-sm max-w-xs">
          <p className="font-semibold">🗺 Карта Пушкиногорья</p>
          {stats && <p className="text-muted-foreground">{stats.total_places} объектов на карте</p>}
          <p className="text-xs text-muted-foreground mt-1">Данные обновляются из OpenStreetMap</p>
        </div>
      </div>

      <div className="w-full lg:w-96 border-l bg-card overflow-y-auto">
        <div className="p-4 space-y-3 border-b">
          <input
            className="w-full rounded-md border px-3 py-2 text-sm"
            placeholder="Поиск..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && loadPlaces()}
          />
          <div className="flex gap-2 flex-wrap">
            <Button size="sm" variant={shopsOnly ? "default" : "outline"} onClick={() => setShopsOnly(!shopsOnly)}>
              🛒 Магазины
            </Button>
            <select className="text-sm rounded-md border px-2 py-1" value={category} onChange={(e) => setCategory(e.target.value)}>
              <option value="">Все категории</option>
              {categories.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
        </div>

        {selected ? (
          <div className="p-4">
            <button className="text-sm text-muted-foreground mb-2" onClick={() => setSelected(null)}>← Назад</button>
            <h3 className="text-lg font-bold">{selected.name}</h3>
            <p className="text-sm text-muted-foreground">{selected.category_label} · {selected.address}</p>
            {selected.avg_rating > 0 && (
              <p className="mt-1">⭐ {selected.avg_rating} · {selected.review_count} отзывов · {selected.complaint_count} жалоб</p>
            )}
            {selected.opening_hours && (
              <div className="text-sm mt-2 bg-amber-50 border border-amber-200 rounded p-2">
                <p className="font-medium">🕐 Время работы:</p>
                <p className="text-muted-foreground">{selected.opening_hours}</p>
              </div>
            )}
            {selected.phone && <p className="text-sm">📞 {selected.phone}</p>}

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
                {selected.reviews.length === 0 && <p className="text-sm text-muted-foreground">Отзывов пока нет</p>}
                {selected.reviews.map((r) => (
                  <div key={r.id} className="text-sm border rounded p-2">
                    <span>{"⭐".repeat(r.rating)}</span> <strong>{r.author_name}</strong>
                    <p className="text-muted-foreground">{r.text}</p>
                  </div>
                ))}
                {selected.recent_complaints.length > 0 && (
                  <div className="mt-4">
                    <p className="text-sm font-medium">Жалобы на цены:</p>
                    {selected.recent_complaints.map((c) => (
                      <div key={c.id} className="text-xs border rounded p-2 mt-1 bg-red-50">
                        <strong>{c.complaint_label}</strong>: {c.description.slice(0, 100)}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {tab === "review" && (
              <div className="mt-3 space-y-3">
                <div>
                  <label className="text-sm">Оценка</label>
                  <select className="w-full border rounded px-2 py-1" value={reviewForm.rating} onChange={(e) => setReviewForm({ ...reviewForm, rating: +e.target.value })}>
                    {[5, 4, 3, 2, 1].map((n) => <option key={n} value={n}>{"⭐".repeat(n)}</option>)}
                  </select>
                </div>
                <textarea className="w-full border rounded p-2 text-sm min-h-[80px]" placeholder="Ваш отзыв..." value={reviewForm.text} onChange={(e) => setReviewForm({ ...reviewForm, text: e.target.value })} />
                <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Ваше имя" value={reviewForm.author_name} onChange={(e) => setReviewForm({ ...reviewForm, author_name: e.target.value })} />
                <Button className="w-full" onClick={submitReview}>Отправить отзыв</Button>
              </div>
            )}

            {tab === "complaint" && (
              <div className="mt-3 space-y-3">
                <p className="text-xs text-muted-foreground">Жалоба на обман с ценниками, чеками, недовес</p>
                <select className="w-full border rounded px-2 py-1 text-sm" value={complaintForm.complaint_type} onChange={(e) => setComplaintForm({ ...complaintForm, complaint_type: e.target.value })}>
                  {complaintTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                </select>
                <div className="grid grid-cols-2 gap-2">
                  <input className="border rounded px-2 py-1 text-sm" placeholder="Цена на ценнике" value={complaintForm.price_tagged} onChange={(e) => setComplaintForm({ ...complaintForm, price_tagged: e.target.value })} />
                  <input className="border rounded px-2 py-1 text-sm" placeholder="Цена на кассе" value={complaintForm.price_charged} onChange={(e) => setComplaintForm({ ...complaintForm, price_charged: e.target.value })} />
                </div>
                <textarea className="w-full border rounded p-2 text-sm min-h-[100px]" placeholder="Опишите ситуацию подробно (мин. 10 символов)..." value={complaintForm.description} onChange={(e) => setComplaintForm({ ...complaintForm, description: e.target.value })} />
                <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Ваше имя" value={complaintForm.author_name} onChange={(e) => setComplaintForm({ ...complaintForm, author_name: e.target.value })} />
                <Button className="w-full" variant="destructive" onClick={submitComplaint}>Подать жалобу</Button>
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 space-y-2 max-h-[60vh] overflow-y-auto">
            {places.slice(0, 50).map((p) => (
              <button key={p.id} className="w-full text-left border rounded p-3 hover:bg-muted/50 text-sm" onClick={() => openPlace(p.id)}>
                <span className="mr-1">{CATEGORY_ICONS[p.category] || "📍"}</span>
                <strong>{p.name}</strong>
                <p className="text-muted-foreground text-xs">{p.category_label} · {p.address}</p>
                {p.complaint_count > 0 && <span className="text-xs text-red-600">{p.complaint_count} жалоб</span>}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
    </div>
  );
}

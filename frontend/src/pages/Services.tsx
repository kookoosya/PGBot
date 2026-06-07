import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { telHref } from "@/components/VkBotLink";
import { api, CatalogItem, ClassifiedAd, ServiceProvider, TimeSlot } from "@/lib/api";
import { getCategoryVisual } from "@/lib/classifiedCategories";
import { PUSHKIN_QUOTES } from "@/lib/pushkin";

const STATUS: Record<string, { label: string; color: string }> = {
  free: { label: "🟢 Свободен", color: "text-green-700" },
  busy: { label: "🔴 Занят", color: "text-red-600" },
  off: { label: "⚫ Выходной", color: "text-gray-500" },
};

const CATALOG_ICONS: Record<string, string> = {
  garden: "🌱", firewood: "🪵", grass_mowing: "🌿", delivery: "🚚",
  handyman: "🔧", snow_removal: "❄️", construction: "🏗", beauty: "💇",
  tutoring: "📚", transport: "🚛", avito: "📢", other: "📋",
};

export function Services() {
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [providers, setProviders] = useState<ServiceProvider[]>([]);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [filter, setFilter] = useState("");
  const [booking, setBooking] = useState<ServiceProvider | null>(null);
  const [serviceId, setServiceId] = useState(0);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [workingHours, setWorkingHours] = useState("");
  const [form, setForm] = useState({ client_name: "", client_phone: "", notes: "" });
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getCatalogCategories().then(setCategories).catch(console.error);
    loadAll();
  }, [filter]);

  const loadAll = () => {
    const params = filter ? { category: filter } : undefined;
    api.getCatalogItems(params).then(setCatalog).catch(console.error);
    api.getServiceClassifieds(filter ? { category: filter } : undefined).then((r) => setAds(r.items)).catch(console.error);
    const p = filter && ["manicure", "haircut", "massage", "brows", "pedicure", "hair_color", "cosmetology", "other"].includes(filter)
      ? { service_type: filter }
      : undefined;
    api.getProviders(p).then(setProviders).catch(console.error);
  };

  const filteredCatalog = useMemo(() => {
    if (!filter) return catalog;
    return catalog.filter((c) => c.category === filter);
  }, [catalog, filter]);

  const filteredAds = useMemo(() => {
    if (!filter) return ads;
    return ads.filter((a) => a.category === filter);
  }, [ads, filter]);

  const openBooking = (p: ServiceProvider) => {
    setBooking(p);
    setServiceId(p.services[0]?.id || 0);
    setSelectedSlot("");
    setMsg("");
    setForm({ client_name: "", client_phone: "", notes: "" });
  };

  const loadSlots = async (sid: number, d: string) => {
    if (!booking || !sid) return;
    const res = await api.getSlots(booking.id, sid, d);
    setSlots(res.slots);
    setWorkingHours(res.working_hours || "");
  };

  useEffect(() => {
    if (booking && serviceId && date) loadSlots(serviceId, date);
  }, [booking, serviceId, date]);

  const submitBooking = async () => {
    if (!booking || !selectedSlot) return;
    setLoading(true);
    try {
      await api.bookAppointment(booking.id, {
        service_id: serviceId,
        appointment_date: date,
        start_time: selectedSlot,
        ...form,
      });
      setMsg("✅ Запись подтверждена!");
      loadAll();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Ошибка записи");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-section max-w-5xl">
      <PageHeader icon="🛠" title="Услуги посёлка" subtitle={PUSHKIN_QUOTES.services}>
        <Link to="/classifieds" className="btn-hero-secondary text-sm">Подать объявление</Link>
        <Link to="/services/register" className="btn-hero-secondary text-sm">Стать мастером</Link>
      </PageHeader>

      <div className="filter-bar mb-6">
        <button type="button" className={`filter-chip ${!filter ? "filter-chip-active" : ""}`} onClick={() => setFilter("")}>Все</button>
        {categories.map((c) => (
          <button key={c.value} type="button" className={`filter-chip ${filter === c.value ? "filter-chip-active" : ""}`} onClick={() => setFilter(c.value)}>
            {CATALOG_ICONS[c.value] || "📋"} {c.label}
          </button>
        ))}
      </div>

      {filteredCatalog.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-bold mb-3">📍 Справочник услуг</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {filteredCatalog.map((item) => (
              <div key={item.id} className="pushkin-card p-4">
                <div className="flex gap-3 items-start">
                  <span className="text-2xl">{CATALOG_ICONS[item.category] || "📋"}</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold">{item.name}</h3>
                    <p className="text-xs text-muted-foreground">{item.category_label}</p>
                    {item.description && <p className="text-sm mt-2">{item.description}</p>}
                    {item.price_hint && <p className="text-sm mt-1 font-medium">{item.price_hint}</p>}
                    {item.address && <p className="text-xs mt-1">📍 {item.address}</p>}
                    <div className="flex flex-wrap gap-2 mt-3">
                      {item.phone && (
                        <a href={telHref(item.phone)} className="btn-hero-primary text-xs px-3 py-1.5 no-underline">
                          📞 Позвонить
                        </a>
                      )}
                      {item.external_url && (
                        <a href={item.external_url} target="_blank" rel="noopener noreferrer" className="btn-hero-secondary text-xs px-3 py-1.5 no-underline">
                          {item.source === "avito" ? "Авито →" : "Подробнее →"}
                        </a>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {filteredAds.length > 0 && (
        <section className="mb-8">
          <h2 className="text-lg font-bold mb-3">📋 Объявления соседей</h2>
          <div className="space-y-3">
            {filteredAds.map((ad) => {
              const visual = getCategoryVisual(ad.category);
              return (
                <div key={ad.id} className="classified-ad-card">
                  <div className="classified-ad-image" style={{ background: visual.gradient }}>
                    <span className="classified-ad-icon">{visual.icon}</span>
                    <span className="classified-ad-badge">{ad.category_label}</span>
                  </div>
                  <div className="classified-ad-body">
                    <h3 className="font-bold">{ad.title}</h3>
                    <p className="text-sm mt-1">{ad.description}</p>
                    {ad.price != null && <p className="text-sm font-medium mt-1">{ad.price} {ad.price_unit || "₽"}</p>}
                    <p className="text-xs text-muted-foreground mt-1">{ad.author_name}</p>
                    <a href={telHref(ad.phone)} className="text-sm font-medium mt-2 inline-block">📞 {ad.phone}</a>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}

      <section>
        <h2 className="text-lg font-bold mb-3">💇 Мастера с онлайн-записью</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {providers.map((p) => (
            <div
              key={p.id}
              className="pushkin-card-hover p-5 cursor-pointer"
              role="button"
              tabIndex={0}
              onClick={() => p.status_today !== "off" && openBooking(p)}
              onKeyDown={(e) => e.key === "Enter" && p.status_today !== "off" && openBooking(p)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-bold text-lg">{p.full_name}</h3>
                  <p className={`text-sm font-medium ${STATUS[p.status_today]?.color}`}>
                    {STATUS[p.status_today]?.label}
                    {p.next_free_slot && ` · ${p.next_free_slot}`}
                  </p>
                </div>
                {p.avg_rating > 0 && <span className="text-sm">⭐ {p.avg_rating}</span>}
              </div>
              {p.address && <p className="text-xs mt-2">📍 {p.address}</p>}
              <div className="mt-3 flex flex-wrap gap-2">
                {p.services.map((s) => (
                  <span key={s.id} className="text-xs bg-secondary rounded-full px-2 py-1">
                    {s.name} {s.price ? `— ${s.price} ₽` : ""}
                  </span>
                ))}
              </div>
              <Button className="w-full mt-4" size="sm" onClick={(e) => { e.stopPropagation(); openBooking(p); }} disabled={p.status_today === "off"}>
                {p.status_today === "off" ? "Выходной" : "Записаться →"}
              </Button>
            </div>
          ))}
          {providers.length === 0 && (
            <p className="col-span-2 text-sm text-muted-foreground py-4">
              Мастеров с записью пока нет — <Link to="/services/register" className="text-primary underline">зарегистрируйтесь</Link>.
            </p>
          )}
        </div>
      </section>

      {booking && (
        <div className="modal-overlay" onClick={() => setBooking(null)}>
          <div className="pushkin-card bg-card p-6 max-w-md w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-bold text-lg">Запись к {booking.full_name}</h3>
            {msg && <p className="text-sm mt-2 text-green-700">{msg}</p>}
            {!msg && (
              <div className="mt-4 space-y-3">
                <select className="w-full border rounded px-3 py-2 text-sm" value={serviceId} onChange={(e) => setServiceId(+e.target.value)}>
                  {booking.services.map((s) => (
                    <option key={s.id} value={s.id}>{s.name} — {s.duration_minutes} мин{s.price ? `, ${s.price} ₽` : ""}</option>
                  ))}
                </select>
                <input type="date" className="w-full border rounded px-3 py-2 text-sm" value={date} min={new Date().toISOString().slice(0, 10)} onChange={(e) => setDate(e.target.value)} />
                {workingHours && <p className="text-xs text-muted-foreground">🕐 {workingHours}</p>}
                <div className="grid grid-cols-4 gap-2">
                  {slots.map((s) => (
                    <button key={s.time} disabled={!s.available} className={`text-sm py-2 rounded border ${selectedSlot === s.time ? "bg-primary text-primary-foreground" : s.available ? "hover:bg-muted" : "opacity-40"}`} onClick={() => s.available && setSelectedSlot(s.time)}>
                      {s.time}
                    </button>
                  ))}
                </div>
                <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Ваше имя" value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })} />
                <input className="w-full border rounded px-3 py-2 text-sm" placeholder="Телефон" value={form.client_phone} onChange={(e) => setForm({ ...form, client_phone: e.target.value })} />
                <Button className="w-full" disabled={!selectedSlot || !form.client_name || !form.client_phone || loading} onClick={submitBooking}>
                  {loading ? "Запись..." : "Подтвердить"}
                </Button>
              </div>
            )}
            <Button variant="outline" className="w-full mt-3" onClick={() => setBooking(null)}>Закрыть</Button>
          </div>
        </div>
      )}
    </div>
  );
}

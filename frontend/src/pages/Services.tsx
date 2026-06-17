import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import {
  LiteraryClassifiedCard,
  LiteraryEmptyState,
  LiteraryProviderCard,
  LiterarySectionHead,
  LiteraryServiceCard,
} from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api/index";
import type { ClassifiedAd } from "@/lib/api/types/classifieds";
import type { CatalogItem } from "@/lib/api/types/places";
import type { ServiceProvider, TimeSlot } from "@/lib/api/types/services";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";

const CATALOG_ICONS: Record<string, string> = {
  garden: "🌱", firewood: "🪵", grass_mowing: "🌿", delivery: "🚚",
  handyman: "🔧", snow_removal: "❄️", construction: "🏗", beauty: "💇",
  tutoring: "📚", transport: "🚛", other: "📋",
};

const copy = PAGE_SECTIONS.services;

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

  const nothingFound = filteredCatalog.length === 0 && filteredAds.length === 0 && providers.length === 0;

  return (
    <div className="literary-page page-section max-w-5xl">
      <PageHeader icon="🛠" title={copy.title} subtitle={copy.lead}>
        <Link to="/classifieds" className="literary-btn literary-btn--ghost text-sm no-underline">Подать объявление</Link>
        <div className="flex flex-wrap gap-2">
          <Link to="/services/cabinet" className="literary-btn literary-btn--ghost text-sm no-underline">Кабинет мастера</Link>
          <Link to="/services/register" className="literary-btn literary-btn--primary text-sm no-underline">Стать мастером</Link>
        </div>
      </PageHeader>

      <section className="page-panel page-panel--forest mb-6">
        <LiterarySectionHead kicker="🔍 Категории" title="Выберите услугу" lead="Покос, дрова, красота, доставка — найдите нужное в посёлке." />
        <div className="literary-filter-bar">
          <button type="button" className={`filter-chip ${!filter ? "filter-chip-active" : ""}`} onClick={() => setFilter("")}>🪶 Все</button>
          {categories.map((c) => (
            <button
              key={c.value}
              type="button"
              className={`filter-chip ${filter === c.value ? "filter-chip-active" : ""}`}
              onClick={() => setFilter(c.value)}
            >
              {CATALOG_ICONS[c.value] || "📋"} {c.label}
            </button>
          ))}
        </div>
      </section>

      {filteredCatalog.length > 0 && (
        <section className="page-panel page-panel--gold mb-6">
          <LiterarySectionHead
            kicker={copy.catalog.kicker}
            title={copy.catalog.title}
            lead={copy.catalog.lead}
          />
          <div className="literary-services-grid">
            {filteredCatalog.map((item) => (
              <LiteraryServiceCard key={item.id} item={item} icon={CATALOG_ICONS[item.category] || "📋"} />
            ))}
          </div>
        </section>
      )}

      {filteredAds.length > 0 && (
        <section className="page-panel page-panel--gold mb-6">
          <LiterarySectionHead
            kicker={copy.ads.kicker}
            title={copy.ads.title}
            lead={copy.ads.lead}
          />
          <div className="literary-classified-list">
            {filteredAds.map((ad) => (
              <LiteraryClassifiedCard key={ad.id} ad={ad} />
            ))}
          </div>
        </section>
      )}

      <section className="page-panel page-panel--forest mb-6">
        <LiterarySectionHead
          kicker={copy.providers.kicker}
          title={copy.providers.title}
          lead={copy.providers.lead}
        />
        {providers.length > 0 ? (
          <div className="literary-providers-grid">
            {providers.map((p) => (
              <LiteraryProviderCard key={p.id} provider={p} onBook={openBooking} />
            ))}
          </div>
        ) : (
          <LiteraryEmptyState {...EMPTY_STATES.providers}>
            <Link to="/services/register" className="literary-btn literary-btn--primary mt-2 no-underline">
              Стать мастером
            </Link>
          </LiteraryEmptyState>
        )}
      </section>

      {filter && nothingFound && (
        <LiteraryEmptyState {...EMPTY_STATES.servicesCatalog} compact />
      )}

      {booking && (
        <div className="literary-modal-overlay" onClick={() => setBooking(null)}>
          <div className="page-panel page-panel--gold literary-booking-modal" onClick={(e) => e.stopPropagation()}>
            <LiterarySectionHead
              kicker="💇 Запись"
              title={booking.full_name}
              lead="Выберите услугу, дату и удобное время."
            />
            {msg && <p className="alert-success">{msg}</p>}
            {!msg && (
              <div className="space-y-3">
                <select className="pushkin-select w-full" value={serviceId} onChange={(e) => setServiceId(+e.target.value)}>
                  {booking.services.map((s) => (
                    <option key={s.id} value={s.id}>{s.name} — {s.duration_minutes} мин{s.price ? `, ${s.price} ₽` : ""}</option>
                  ))}
                </select>
                <input type="date" className="pushkin-select w-full" value={date} min={new Date().toISOString().slice(0, 10)} onChange={(e) => setDate(e.target.value)} />
                {workingHours && <p className="landing-muted text-xs m-0">🕐 {workingHours}</p>}
                <div className="literary-slot-grid">
                  {slots.map((s) => (
                    <button
                      key={s.time}
                      type="button"
                      disabled={!s.available}
                      className={`literary-slot-btn${selectedSlot === s.time ? " literary-slot-btn--active" : ""}${!s.available ? " literary-slot-btn--disabled" : ""}`}
                      onClick={() => s.available && setSelectedSlot(s.time)}
                    >
                      {s.time}
                    </button>
                  ))}
                </div>
                <Input placeholder="Ваше имя" value={form.client_name} onChange={(e) => setForm({ ...form, client_name: e.target.value })} />
                <Input placeholder="Телефон" value={form.client_phone} onChange={(e) => setForm({ ...form, client_phone: e.target.value })} />
                <button
                  type="button"
                  className="literary-btn literary-btn--primary w-full"
                  disabled={!selectedSlot || !form.client_name || !form.client_phone || loading}
                  onClick={submitBooking}
                >
                  {loading ? "Запись…" : "Подтвердить"}
                </button>
              </div>
            )}
            <button type="button" className="literary-btn literary-btn--ghost w-full mt-3" onClick={() => setBooking(null)}>
              Закрыть
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

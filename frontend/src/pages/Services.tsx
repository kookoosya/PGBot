import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { ServiceSectionTabs } from "@/components/services/ServiceSectionTabs";
import {
  LiteraryClassifiedCard,
  LiteraryEmptyState,
  LiteraryInlineLoader,
  LiteraryProviderCard,
  LiterarySectionHead,
  LiteraryServiceCard,
} from "@/components/literary";
import { Input } from "@/components/ui/input";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { api } from "@/lib/api/index";
import type { ClassifiedAd } from "@/lib/api/types/classifieds";
import type { CatalogItem } from "@/lib/api/types/places";
import type { ServiceProvider, TimeSlot } from "@/lib/api/types/services";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";
import {
  showsAds,
  showsCatalog,
  showsProviders,
  type ServiceTabId,
} from "@/lib/servicesBoard";

const CATALOG_ICONS: Record<string, string> = {
  garden: "🌱",
  firewood: "🪵",
  grass_mowing: "🌿",
  delivery: "🚚",
  handyman: "🔧",
  snow_removal: "❄️",
  construction: "🏗",
  beauty: "💇",
  tutoring: "📚",
  transport: "🚛",
  other: "📋",
};

const BEAUTY_PROVIDER_TYPES = new Set([
  "manicure",
  "haircut",
  "massage",
  "brows",
  "pedicure",
  "hair_color",
  "cosmetology",
  "other",
]);

const copy = PAGE_SECTIONS.services;

const FLOW_STEPS = [
  { icon: "📍", title: "Справочник", text: "Проверенные телефоны — покос, дрова, доставка." },
  { icon: "🤝", title: "Соседи", text: "Объявления жителей с контактами в карточке." },
  { icon: "💇", title: "Запись", text: "Мастера красоты — онлайн-запись на услугу." },
];

function matchSearch(text: string, q: string) {
  if (!q) return true;
  return text.toLowerCase().includes(q.toLowerCase());
}

export function Services() {
  useDocumentTitle(copy.title);

  const [activeTab, setActiveTab] = useState<ServiceTabId>("all");
  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [ads, setAds] = useState<ClassifiedAd[]>([]);
  const [providers, setProviders] = useState<ServiceProvider[]>([]);
  const [categories, setCategories] = useState<{ value: string; label: string }[]>([]);
  const [filter, setFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [booking, setBooking] = useState<ServiceProvider | null>(null);
  const [serviceId, setServiceId] = useState(0);
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [workingHours, setWorkingHours] = useState("");
  const [form, setForm] = useState({ client_name: "", client_phone: "", notes: "" });
  const [msg, setMsg] = useState("");
  const [bookingLoading, setBookingLoading] = useState(false);

  const reload = useCallback(() => setReloadToken((t) => t + 1), []);

  useEffect(() => {
    const t = window.setTimeout(() => setSearch(searchInput.trim()), 400);
    return () => window.clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    api.getCatalogCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    const params = filter ? { category: filter } : undefined;
    const providerParams =
      filter && BEAUTY_PROVIDER_TYPES.has(filter) ? { service_type: filter } : undefined;

    setLoading(true);
    setLoadError(false);
    Promise.all([
      api.getCatalogItems(params),
      api.getServiceClassifieds(filter ? { category: filter } : undefined),
      api.getProviders(providerParams),
    ])
      .then(([cat, adsRes, prov]) => {
        setCatalog(cat);
        setAds(adsRes.items);
        setProviders(prov);
      })
      .catch(() => {
        setCatalog([]);
        setAds([]);
        setProviders([]);
        setLoadError(true);
      })
      .finally(() => setLoading(false));
  }, [filter, reloadToken]);

  const filteredCatalog = useMemo(
    () => catalog.filter((c) => matchSearch(`${c.name} ${c.description || ""} ${c.address || ""}`, search)),
    [catalog, search],
  );

  const filteredAds = useMemo(
    () => ads.filter((a) => matchSearch(`${a.title} ${a.description || ""}`, search)),
    [ads, search],
  );

  const filteredProviders = useMemo(() => {
    if (!search) return providers;
    return providers.filter((p) =>
      matchSearch(`${p.full_name} ${p.services.map((s) => s.name).join(" ")}`, search),
    );
  }, [providers, search]);

  const tabCounts = useMemo(
    () => ({
      all: filteredCatalog.length + filteredAds.length + filteredProviders.length,
      catalog: filteredCatalog.length,
      ads: filteredAds.length,
      providers: filteredProviders.length,
    }),
    [filteredCatalog.length, filteredAds.length, filteredProviders.length],
  );

  const visibleCount =
    activeTab === "catalog"
      ? filteredCatalog.length
      : activeTab === "ads"
        ? filteredAds.length
        : activeTab === "providers"
          ? filteredProviders.length
          : tabCounts.all;

  const emptyState = search || filter ? EMPTY_STATES.servicesCatalog : EMPTY_STATES.services;
  const nothingFound = !loading && !loadError && visibleCount === 0;

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
    setBookingLoading(true);
    try {
      await api.bookAppointment(booking.id, {
        service_id: serviceId,
        appointment_date: date,
        start_time: selectedSlot,
        ...form,
      });
      setMsg("✅ Запись подтверждена!");
      reload();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Ошибка записи");
    } finally {
      setBookingLoading(false);
    }
  };

  return (
    <div className="literary-page page-section max-w-5xl">
      <PageHeader icon="🛠" title={copy.title} subtitle={copy.lead}>
        <Link to="/classifieds/services?new=1" className="literary-btn literary-btn--ghost text-sm no-underline">
          Подать объявление
        </Link>
        <Link to="/services/register" className="literary-btn literary-btn--primary text-sm no-underline">
          Стать мастером
        </Link>
      </PageHeader>

      <ServiceSectionTabs active={activeTab} onChange={setActiveTab} counts={tabCounts} />

      <section className="page-panel page-panel--gold mb-4" aria-label="Откуда берутся услуги">
        <div className="complaints-flow">
          {FLOW_STEPS.map((step) => (
            <div key={step.title} className="complaints-flow-step">
              <span className="complaints-flow-icon" aria-hidden>{step.icon}</span>
              <div>
                <p className="complaints-flow-title m-0">{step.title}</p>
                <p className="complaints-flow-text m-0">{step.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {!loadError && tabCounts.all > 0 && (
        <div className="page-section pb-2">
          <div className="map-stats-ribbon" aria-label="Статистика услуг">
            <div className="map-stats-ribbon-head">
              <p className="map-stats-ribbon-total m-0">
                <strong>{visibleCount}</strong>{" "}
                {filter || search ? "в выбранной категории" : "услуг и мастеров"}
              </p>
              <p className="map-stats-ribbon-sync m-0">
                Справочник {tabCounts.catalog} · соседи {tabCounts.ads} · запись {tabCounts.providers}
              </p>
            </div>
          </div>
        </div>
      )}

      <section className="page-panel page-panel--forest mb-6">
        <LiterarySectionHead kicker="🔍 Поиск" title="Найти услугу" lead="Покос, дрова, маникюр, доставка…" compact />
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <Input
            placeholder="Введите слово из названия или описания"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="flex-1 pushkin-select"
          />
          {search && (
            <button
              type="button"
              className="literary-btn literary-btn--ghost shrink-0 text-sm"
              onClick={() => {
                setSearch("");
                setSearchInput("");
              }}
            >
              Сбросить
            </button>
          )}
          <button type="button" className="literary-btn literary-btn--ghost shrink-0" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </button>
        </div>
        <div className="literary-filter-bar">
          <button type="button" className={`filter-chip ${!filter ? "filter-chip-active" : ""}`} onClick={() => setFilter("")}>
            🪶 Все
          </button>
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

      {loadError && !loading && (
        <LiteraryEmptyState icon="⚠️" title="Справочник временно недоступен" text="Не удалось загрузить услуги. Попробуйте ещё раз.">
          <button type="button" className="literary-btn literary-btn--primary mt-3" onClick={reload}>
            Повторить
          </button>
        </LiteraryEmptyState>
      )}

      {loading && <LiteraryInlineLoader label="Загружаем услуги…" />}

      {!loadError && !loading && nothingFound && (
        <LiteraryEmptyState {...emptyState}>
          <Link to="/classifieds/services?new=1" className="literary-btn literary-btn--primary mt-2 no-underline">
            Подать объявление
          </Link>
        </LiteraryEmptyState>
      )}

      {!loadError && !loading && showsCatalog(activeTab) && filteredCatalog.length > 0 && (
        <section className="page-panel page-panel--gold mb-6">
          <LiterarySectionHead kicker={copy.catalog.kicker} title={copy.catalog.title} lead={copy.catalog.lead} />
          <div className="literary-services-grid">
            {filteredCatalog.map((item) => (
              <LiteraryServiceCard key={item.id} item={item} icon={CATALOG_ICONS[item.category] || "📋"} />
            ))}
          </div>
        </section>
      )}

      {!loadError && !loading && showsAds(activeTab) && filteredAds.length > 0 && (
        <section className="page-panel page-panel--gold mb-6">
          <LiterarySectionHead kicker={copy.ads.kicker} title={copy.ads.title} lead={copy.ads.lead} />
          <div className="literary-classified-list">
            {filteredAds.map((ad) => (
              <LiteraryClassifiedCard key={ad.id} ad={ad} />
            ))}
          </div>
        </section>
      )}

      {!loadError && !loading && showsProviders(activeTab) && (
        <section className="page-panel page-panel--forest mb-6">
          <LiterarySectionHead kicker={copy.providers.kicker} title={copy.providers.title} lead={copy.providers.lead} />
          {filteredProviders.length > 0 ? (
            <div className="literary-providers-grid">
              {filteredProviders.map((p) => (
                <LiteraryProviderCard key={p.id} provider={p} onBook={openBooking} />
              ))}
            </div>
          ) : (
            activeTab === "providers" && (
              <LiteraryEmptyState {...EMPTY_STATES.providers}>
                <Link to="/services/register" className="literary-btn literary-btn--primary mt-2 no-underline">
                  Стать мастером
                </Link>
              </LiteraryEmptyState>
            )
          )}
        </section>
      )}

      {booking && (
        <div className="literary-modal-overlay" onClick={() => setBooking(null)}>
          <div className="page-panel page-panel--gold literary-booking-modal" onClick={(e) => e.stopPropagation()}>
            <LiterarySectionHead kicker="💇 Запись" title={booking.full_name} lead="Выберите услугу, дату и удобное время." />
            {msg && <p className="alert-success">{msg}</p>}
            {!msg && (
              <div className="space-y-3">
                <select className="pushkin-select w-full" value={serviceId} onChange={(e) => setServiceId(+e.target.value)}>
                  {booking.services.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} — {s.duration_minutes} мин{s.price ? `, ${s.price} ₽` : ""}
                    </option>
                  ))}
                </select>
                <input
                  type="date"
                  className="pushkin-select w-full"
                  value={date}
                  min={new Date().toISOString().slice(0, 10)}
                  onChange={(e) => setDate(e.target.value)}
                />
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
                  disabled={!selectedSlot || !form.client_name || !form.client_phone || bookingLoading}
                  onClick={submitBooking}
                >
                  {bookingLoading ? "Запись…" : "Подтвердить"}
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

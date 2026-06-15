import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { CinemaSpotlight, EventCard, LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, EventRegion, PublicEvent } from "@/lib/api";
import { isCinemaEvent } from "@/lib/eventUtils";
import { EMPTY_STATES } from "@/lib/literaryCopy";

type RegionFilter = "all" | EventRegion;

const REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

export function EventsPage() {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    api
      .getPublicEvents({
        region: regionFilter === "all" ? undefined : regionFilter,
        search: search || undefined,
        limit: "40",
      })
      .then((r) => setEvents(r.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [regionFilter, search]);

  const categoryFilters = useMemo(() => {
    const cats = new Set(events.map((e) => e.category_label));
    return Array.from(cats).sort();
  }, [events]);

  const [categoryFilter, setCategoryFilter] = useState("");

  const visibleEvents = useMemo(() => {
    if (!categoryFilter) return events;
    return events.filter((e) => e.category_label === categoryFilter);
  }, [events, categoryFilter]);

  const cinemaEvents = useMemo(
    () => visibleEvents.filter(isCinemaEvent),
    [visibleEvents],
  );
  const pushkinEvents = useMemo(
    () => visibleEvents.filter((e) => e.region_label === "Пушкинские Горы" && !isCinemaEvent(e)),
    [visibleEvents],
  );
  const pskovEvents = useMemo(
    () => visibleEvents.filter((e) => e.region_label === "Псков" && !isCinemaEvent(e)),
    [visibleEvents],
  );
  const showCinemaBlock = cinemaEvents.length > 0 && regionFilter !== "pushkin_gory";

  return (
    <div className="page-section max-w-5xl">
      <PageHeader
        icon="📅"
        title="Афиша Пушкиногорья"
        subtitle="От площади Ленина до кинозалов Пскова — культурная жизнь края в одном месте"
      />

      <div className="page-panel page-panel--forest mb-6">
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <Input
            placeholder="Поиск: концерт, кино, ярмарка…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="flex-1 pushkin-select"
          />
          <button type="button" className="literary-btn literary-btn--primary" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </button>
        </div>

        <div className="events-region-filters mb-0" role="group" aria-label="Регион">
          {REGION_FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={`events-region-filter${regionFilter === item.id ? " events-region-filter--active" : ""}`}
              onClick={() => setRegionFilter(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>

        {categoryFilters.length > 1 && (
          <div className="filter-bar mt-4">
            <button
              type="button"
              className={`filter-chip${!categoryFilter ? " filter-chip-active" : ""}`}
              onClick={() => setCategoryFilter("")}
            >
              Все категории
            </button>
            {categoryFilters.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`filter-chip${categoryFilter === cat ? " filter-chip-active" : ""}`}
                onClick={() => setCategoryFilter(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading ? (
        <p className="events-muted">Собираем афишу…</p>
      ) : visibleEvents.length === 0 ? (
        <LiteraryEmptyState {...EMPTY_STATES.events} />
      ) : (
        <div className="literary-dashboard">
          {showCinemaBlock && (
            <CinemaSpotlight linkTo="/events">
              <ol className="events-grid events-grid--cinema">
                {cinemaEvents.map((event) => (
                  <EventCard key={event.id} event={event} spotlight />
                ))}
              </ol>
            </CinemaSpotlight>
          )}

          {pushkinEvents.length > 0 && regionFilter !== "pskov" && (
            <section className="page-panel page-panel--forest">
              <LiterarySectionHead
                kicker="🪶 Посёлок"
                title="В Пушкинских Горах"
                lead="Праздники, концерты и встречи у НКЦ и на площади."
              />
              <ol className="events-grid events-grid--wide">
                {pushkinEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </ol>
            </section>
          )}

          {pskovEvents.length > 0 && regionFilter !== "pushkin_gory" && (
            <section className="page-panel page-panel--gold">
              <LiterarySectionHead
                kicker="🏛 Псков"
                title="Мероприятия в городе"
                lead="Концерты, выставки и городские праздники."
              />
              <ol className="events-grid">
                {pskovEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </ol>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

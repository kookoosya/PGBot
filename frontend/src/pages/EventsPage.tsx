import { useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/PageHeader";
import { CinemaSpotlight, EventCard, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, EventRegion, PublicEvent } from "@/lib/api";
import { groupEventsByShow, isRealCinemaEvent } from "@/lib/eventUtils";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";

type RegionFilter = "all" | EventRegion;

const REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

const copy = PAGE_SECTIONS.events;

export function EventsPage() {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    setLoadError(false);
    api
      .getPublicEvents({
        region: regionFilter === "all" ? undefined : regionFilter,
        search: search || undefined,
        limit: "40",
      })
      .then((r) => setEvents(r.items))
      .catch(() => {
        setEvents([]);
        setLoadError(true);
      })
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
    () => groupEventsByShow(visibleEvents.filter(isRealCinemaEvent)),
    [visibleEvents],
  );
  const pushkinEvents = useMemo(
    () => visibleEvents.filter((e) => e.region_label === "Пушкинские Горы" && !isRealCinemaEvent(e)),
    [visibleEvents],
  );
  const pskovEvents = useMemo(
    () => visibleEvents.filter((e) => e.region_label === "Псков" && !isRealCinemaEvent(e)),
    [visibleEvents],
  );
  const showCinemaBlock = regionFilter !== "pushkin_gory";

  return (
    <div className="literary-page page-section max-w-5xl">
      <PageHeader icon="📅" title={copy.title} subtitle={copy.lead} />

      <section className="page-panel page-panel--gold mb-6">
        <LiterarySectionHead
          kicker="🔍 Поиск"
          title="Найти в афише"
          compact
        />
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <Input
            placeholder="Поиск: концерт, кино, ярмарка…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="flex-1 pushkin-select"
          />
          <button type="button" className="literary-btn literary-btn--primary shrink-0" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </button>
          {search && (
            <button
              type="button"
              className="literary-btn literary-btn--ghost shrink-0 text-sm"
              onClick={() => { setSearch(""); setSearchInput(""); }}
            >
              Сбросить
            </button>
          )}
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
          <div className="literary-filter-bar mt-4">
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
      </section>

      {loading ? (
        <LiteraryInlineLoader label="Собираем афишу Пушкиногорья…" />
      ) : loadError ? (
        <LiteraryEmptyState
          icon="⚠️"
          title="Афиша временно недоступна"
          text="Не удалось загрузить события. Попробуйте обновить страницу через минуту."
        />
      ) : visibleEvents.length === 0 ? (
        <LiteraryEmptyState {...(search ? EMPTY_STATES.eventsSearch : EMPTY_STATES.events)} />
      ) : (
        <div className="literary-dashboard">
          {showCinemaBlock && (
            <CinemaSpotlight linkTo="/events" linkLabel="Все сеансы →" empty={cinemaEvents.length === 0}>
              {cinemaEvents.length > 0 ? (
                <ol className="events-grid events-grid--cinema">
                  {cinemaEvents.map((event) => (
                    <EventCard key={event.id} event={event} spotlight />
                  ))}
                </ol>
              ) : (
                <LiteraryEmptyState {...EMPTY_STATES.cinema} compact tone="dark" />
              )}
            </CinemaSpotlight>
          )}

          {pushkinEvents.length > 0 && regionFilter !== "pskov" && (
            <section className="page-panel page-panel--forest">
              <LiterarySectionHead
                kicker={copy.pushkin.kicker}
                title={copy.pushkin.title}
                compact
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
                kicker={copy.pskov.kicker}
                title={copy.pskov.title}
                compact
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

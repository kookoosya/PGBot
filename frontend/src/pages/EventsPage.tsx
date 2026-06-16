import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { CinemaSpotlight, EventCard, FestivalProgramBlock, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { api, PublicEvent } from "@/lib/api";
import { EVENT_REGION_FILTERS, parseRegionParam, type RegionFilter } from "@/lib/eventRegionFilters";
import { groupEventsByShow, isRealCinemaEvent, mergePublicEvents, partitionGarnectProgram } from "@/lib/eventUtils";
import { EMPTY_STATES, PAGE_SECTIONS } from "@/lib/literaryCopy";

const copy = PAGE_SECTIONS.events;

export function EventsPage() {
  const [searchParams] = useSearchParams();
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  // По умолчанию — посёлок, но кино и Псков всё равно подтягиваем в верхний блок.
  const [regionFilter, setRegionFilter] = useState<RegionFilter>(() => parseRegionParam(searchParams.get("region")));
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    setLoadError(false);

    const base = { search: search || undefined, limit: "80" as const };

    const load =
      regionFilter === "pskov"
        ? api.getPublicEvents({ ...base, region: "pskov" }).then((r) => r.items)
        : Promise.all([
            api.getPublicEvents({ ...base, region: "pushkin_gory" }),
            api.getPublicEvents({ ...base, region: "pskov" }),
          ]).then(([pushkin, pskov]) => mergePublicEvents(pskov.items, pushkin.items));

    load
      .then(setEvents)
      .catch(() => {
        setEvents([]);
        setLoadError(true);
      })
      .finally(() => setLoading(false));
  }, [regionFilter, search]);

  const categoryFilters = useMemo(() => {
    const pushkinCats = new Set(
      events
        .filter((e) => e.region_label === "Пушкинские Горы")
        .map((e) => e.category_label)
        .filter(Boolean),
    );
    const allCats = new Set(events.map((e) => e.category_label).filter(Boolean));

    // "Все категории" — начинаем с тех, что встречаются в Пушкинских Горах.
    const pushkinOrdered = Array.from(pushkinCats).sort();
    const remaining = Array.from(allCats)
      .filter((c) => !pushkinCats.has(c))
      .sort();
    return [...pushkinOrdered, ...remaining];
  }, [events]);

  const [categoryFilter, setCategoryFilter] = useState("");

  useEffect(() => {
    if (categoryFilter && !categoryFilters.includes(categoryFilter)) {
      setCategoryFilter("");
    }
  }, [categoryFilter, categoryFilters]);

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
  const { program: garnectProgram, rest: pushkinOtherEvents } = useMemo(
    () => partitionGarnectProgram(pushkinEvents),
    [pushkinEvents],
  );
  const pskovEvents = useMemo(
    () => visibleEvents.filter((e) => e.region_label === "Псков" && !isRealCinemaEvent(e)),
    [visibleEvents],
  );
  const showPushkinBlock = pushkinEvents.length > 0 && regionFilter !== "pskov";
  const showCityRow = regionFilter !== "pskov" && (cinemaEvents.length > 0 || pskovEvents.length > 0);
  const showPskovOnlyBlock = regionFilter === "pskov" && pskovEvents.length > 0;

  const cinemaBlock = (
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
  );

  const pskovBlock = (
    <section className="page-panel page-panel--gold events-city-pskov">
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
  );

  return (
    <div className="literary-page page-section max-w-6xl events-page">
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
          {EVENT_REGION_FILTERS.map((item) => (
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
          {showCityRow && (
            <div className="events-city-row">
              {cinemaBlock}
              {pskovEvents.length > 0 && pskovBlock}
            </div>
          )}

          {regionFilter === "pskov" && cinemaBlock}

          {showPskovOnlyBlock && pskovBlock}

          {showPushkinBlock && (
            <section className="page-panel page-panel--forest">
              <LiterarySectionHead
                kicker={copy.pushkin.kicker}
                title={copy.pushkin.title}
                compact
              />
              <ol className="events-grid events-grid--wide">
                {garnectProgram.length > 0 && (
                  <li className="events-festival-program-wrap">
                    <FestivalProgramBlock events={garnectProgram} />
                  </li>
                )}
                {pushkinOtherEvents.map((event) => (
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

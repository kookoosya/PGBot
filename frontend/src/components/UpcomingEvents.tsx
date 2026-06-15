import { useMemo, useState } from "react";
import { EventCard, LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { type EventRegion } from "@/lib/api";
import { isCinemaEvent } from "@/lib/eventUtils";
import { useToday } from "@/hooks/useToday";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type RegionFilter = "all" | EventRegion;

const REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

export function UpcomingEvents() {
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const apiRegion = regionFilter === "all" ? undefined : regionFilter;
  const { data, loading } = useToday(apiRegion);
  const events = data?.upcoming_events ?? [];

  const filteredEvents = useMemo(() => {
    let list = events;
    if (regionFilter !== "all") {
      const label = regionFilter === "pskov" ? "Псков" : "Пушкинские Горы";
      list = list.filter((event) => event.region_label === label);
    }
    const q = searchInput.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (e) =>
          e.title.toLowerCase().includes(q) ||
          (e.description?.toLowerCase().includes(q) ?? false) ||
          e.category_label.toLowerCase().includes(q),
      );
    }
    return list;
  }, [events, regionFilter, searchInput]);

  const pushkinEvents = useMemo(
    () => filteredEvents.filter((e) => e.region_label === "Пушкинские Горы" && !isCinemaEvent(e)),
    [filteredEvents],
  );
  const cinemaEvents = useMemo(
    () => filteredEvents.filter((e) => isCinemaEvent(e)),
    [filteredEvents],
  );
  const otherPskovEvents = useMemo(
    () => filteredEvents.filter((e) => e.region_label === "Псков" && !isCinemaEvent(e)),
    [filteredEvents],
  );

  const showSplit = regionFilter === "all" && !searchInput.trim();

  return (
    <div className="literary-dashboard">
      <section className="page-panel page-panel--forest" aria-label="Ближайшее в Пушкиногорье">
        <LiterarySectionHead
          kicker="📅 Афиша посёлка"
          title="Ближайшее в Пушкиногорье"
          lead="Концерты, праздники и встречи в рп. Пушкинские Горы — для жителей и гостей музея-заповедника."
          linkTo="/events"
          linkLabel="Вся афиша →"
        />

        <div className="events-toolbar mb-4">
          <div className="events-region-filters events-region-filters--inline" role="group" aria-label="Фильтр по региону">
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
          <div className="events-search-row">
            <Input
              placeholder="Поиск по афише…"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="events-search-input pushkin-select"
            />
            {searchInput && (
              <Button type="button" variant="outline" size="sm" onClick={() => setSearchInput("")}>
                Сброс
              </Button>
            )}
          </div>
        </div>

        {loading && !data ? (
          <p className="events-muted">Загружаем афишу…</p>
        ) : showSplit ? (
          pushkinEvents.length === 0 ? (
            <LiteraryEmptyState
              icon="🎭"
              title="Афиша готовится"
              text="Скоро здесь появятся концерты, ярмарки и праздники в посёлке."
              verse="«И долго буду тем любезен я народу…»"
            />
          ) : (
            <ol className="events-grid events-grid--wide">
              {pushkinEvents.map((event) => (
                <EventCard key={event.id} event={event} descLimit={120} />
              ))}
            </ol>
          )
        ) : filteredEvents.length === 0 ? (
          <LiteraryEmptyState
            icon="🔍"
            title="Ничего не найдено"
            text="Попробуйте другой запрос или смените регион."
          />
        ) : (
          <ol className="events-grid events-grid--wide">
            {filteredEvents.map((event) => (
              <EventCard key={event.id} event={event} descLimit={120} />
            ))}
          </ol>
        )}
      </section>

      {showSplit && cinemaEvents.length > 0 && (
        <section className="page-panel page-panel--gold" aria-label="Кино в Пскове">
          <LiterarySectionHead
            kicker="🎬 Кинотеатры"
            title="Кино в Пскове"
            lead="Сеансы в городе — удобно совместить с поездкой из Пушкинских Гор."
            linkTo="/events?region=pskov"
            linkLabel="Все сеансы →"
          />
          <ol className="events-grid events-grid--cinema">
            {cinemaEvents.map((event) => (
              <EventCard key={event.id} event={event} descLimit={100} />
            ))}
          </ol>
        </section>
      )}

      {showSplit && otherPskovEvents.length > 0 && (
        <section className="page-panel page-panel--gold" aria-label="События в Пскове">
          <LiterarySectionHead
            kicker="🏛 Псков"
            title="В Пскове"
            lead="Концерты и мероприятия в областном центре."
            linkTo="/events?region=pskov"
            linkLabel="Афиша Пскова →"
          />
          <ol className="events-grid">
            {otherPskovEvents.map((event) => (
              <EventCard key={event.id} event={event} descLimit={100} />
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}

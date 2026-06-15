import { useMemo, useState } from "react";
import { CinemaSpotlight, EventCard, LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import { type EventRegion } from "@/lib/api";
import { isCinemaEvent } from "@/lib/eventUtils";
import { EMPTY_STATES, LANDING_SECTIONS } from "@/lib/literaryCopy";
import { useToday } from "@/hooks/useToday";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type RegionFilter = "all" | EventRegion;

const REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

const LANDING_LIMITS = {
  pushkin: 3,
  cinema: 2,
  pskov: 2,
} as const;

interface UpcomingEventsProps {
  /** Компактный вид для главной — без поиска, с лимитами */
  variant?: "default" | "landing";
}

export function UpcomingEvents({ variant = "default" }: UpcomingEventsProps) {
  const isLanding = variant === "landing";
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

  const showSplit = (isLanding || (regionFilter === "all" && !searchInput.trim()));

  const displayPushkin = isLanding ? pushkinEvents.slice(0, LANDING_LIMITS.pushkin) : pushkinEvents;
  const displayCinema = isLanding ? cinemaEvents.slice(0, LANDING_LIMITS.cinema) : cinemaEvents;
  const displayPskov = isLanding ? otherPskovEvents.slice(0, LANDING_LIMITS.pskov) : otherPskovEvents;

  const eventsCopy = LANDING_SECTIONS.events;
  const pskovCopy = LANDING_SECTIONS.pskov;

  return (
    <div className={isLanding ? "landing-events" : "literary-dashboard"}>
      <section className="page-panel page-panel--forest landing-block" aria-label="Ближайшее в Пушкиногорье">
        <LiterarySectionHead
          kicker={isLanding ? eventsCopy.kicker : "🪶 Пушкиногорье"}
          title={isLanding ? eventsCopy.title : "Ближайшее в посёлке"}
          lead={
            isLanding
              ? eventsCopy.lead
              : "Концерты у НКЦ, праздники на площади, встречи музея-заповедника — жизнь рп. Пушкинские Горы."
          }
          linkTo="/events"
          linkLabel="Вся афиша →"
        />

        {!isLanding && (
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
        )}

        {loading && !data ? (
          <p className="landing-muted">Собираем афишу Пушкиногорья…</p>
        ) : showSplit ? (
          displayPushkin.length === 0 ? (
            <LiteraryEmptyState {...EMPTY_STATES.events} compact={isLanding} />
          ) : (
            <ol className={`events-grid${isLanding ? "" : " events-grid--wide"}`}>
              {displayPushkin.map((event) => (
                <EventCard key={event.id} event={event} descLimit={isLanding ? 100 : 120} />
              ))}
            </ol>
          )
        ) : filteredEvents.length === 0 ? (
          <LiteraryEmptyState {...EMPTY_STATES.eventsSearch} />
        ) : (
          <ol className="events-grid events-grid--wide">
            {filteredEvents.map((event) => (
              <EventCard key={event.id} event={event} descLimit={120} spotlight={isCinemaEvent(event)} />
            ))}
          </ol>
        )}
      </section>

      {showSplit && displayCinema.length > 0 && (
        <CinemaSpotlight featured={isLanding}>
          <ol className={`events-grid events-grid--cinema${isLanding ? " events-grid--cinema-landing" : ""}`}>
            {displayCinema.map((event, index) => (
              <EventCard
                key={event.id}
                event={event}
                descLimit={isLanding ? 90 : 100}
                spotlight
                className={isLanding && index === 0 ? "event-card-landing-featured" : ""}
              />
            ))}
          </ol>
        </CinemaSpotlight>
      )}

      {showSplit && displayPskov.length > 0 && (
        <section className="page-panel page-panel--gold landing-block" aria-label="События в Пскове">
          <LiterarySectionHead
            kicker={pskovCopy.kicker}
            title={pskovCopy.title}
            lead={pskovCopy.lead}
            linkTo="/events?region=pskov"
            linkLabel="Афиша Пскова →"
          />
          <ol className="events-grid">
            {displayPskov.map((event) => (
              <EventCard key={event.id} event={event} descLimit={isLanding ? 90 : 100} />
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}

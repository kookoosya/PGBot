import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CinemaSpotlight, EventCard, FestivalProgramBlock, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { ctaArrow, CTA } from "@/lib/cta";
import { usePushkinGarnectProgram } from "@/hooks/usePushkinGarnectProgram";
import { useSiteInfo } from "@/hooks/useSiteInfo";
import { isRealCinemaEvent, groupEventsByShow, partitionGarnectProgram } from "@/lib/eventUtils";
import { EVENT_REGION_FILTERS, type RegionFilter } from "@/lib/eventRegionFilters";
import { absoluteGarnectEventsUrl, garnectEventsPath } from "@/lib/festivalFilters";
import { EMPTY_STATES, LANDING_SECTIONS } from "@/lib/literaryCopy";
import { landingGridCountClass } from "@/lib/landingLayout";
import { siteOrigin } from "@/lib/siteUrl";
import { useToday } from "@/hooks/useToday";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const LANDING_LIMITS = {
  pushkin: 3,
  pskov: 2,
} as const;

interface UpcomingEventsProps {
  /** Компактный вид для главной — без поиска, с лимитами */
  variant?: "default" | "landing";
}

export function UpcomingEvents({ variant = "default" }: UpcomingEventsProps) {
  const isLanding = variant === "landing";
  const { info } = useSiteInfo();
  const garnectShareUrl = absoluteGarnectEventsUrl(info?.site_url ?? siteOrigin());
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const { program: landingGarnect, rest: landingPushkinRest, loading: landingGarnectLoading } =
    usePushkinGarnectProgram(isLanding);
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

  const pushkinEvents = useMemo(() => {
    if (isLanding) {
      return [...landingGarnect, ...landingPushkinRest];
    }
    return filteredEvents.filter(
      (event) => event.region_label === "Пушкинские Горы" && !isRealCinemaEvent(event),
    );
  }, [filteredEvents, isLanding, landingGarnect, landingPushkinRest]);

  const { program: garnectProgram, rest: pushkinOtherEvents } = useMemo(
    () => partitionGarnectProgram(pushkinEvents),
    [pushkinEvents],
  );
  const cinemaEvents = useMemo(
    () => groupEventsByShow(filteredEvents.filter(isRealCinemaEvent)),
    [filteredEvents],
  );
  const otherPskovEvents = useMemo(
    () => filteredEvents.filter((e) => e.region_label === "Псков" && !isRealCinemaEvent(e)),
    [filteredEvents],
  );

  const showSplit = isLanding || (regionFilter === "all" && !searchInput.trim());

  const displayPushkin = isLanding ? pushkinOtherEvents.slice(0, LANDING_LIMITS.pushkin) : pushkinOtherEvents;
  const displayCinema = isLanding ? [] : cinemaEvents;
  const displayPskov = isLanding ? otherPskovEvents.slice(0, LANDING_LIMITS.pskov) : otherPskovEvents;

  const eventsCopy = LANDING_SECTIONS.events;
  const pskovCopy = LANDING_SECTIONS.pskov;
  const showCityRow = !isLanding && showSplit && (displayCinema.length > 0 || displayPskov.length > 0);
  const cinemaSingle = isLanding && displayCinema.length === 1;

  const pushkinSection = (
    <section className="page-panel page-panel--forest landing-block" aria-label="Ближайшее в Пушкиногорье">
      <LiterarySectionHead
        kicker={isLanding ? eventsCopy.kicker : "🪶 Пушкиногорье"}
        title={isLanding ? eventsCopy.title : "Ближайшее в посёлке"}
        lead={
          isLanding
            ? undefined
            : "Концерты у НКЦ, праздники на площади, встречи музея-заповедника — жизнь рп. Пушкинские Горы."
        }
        compact={isLanding}
        linkTo="/events"
        linkLabel={ctaArrow(CTA.allEvents)}
      />

      {!isLanding && (
        <div className="events-toolbar mb-4">
          <div className="events-region-filters events-region-filters--inline" role="group" aria-label="Фильтр по региону">
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

      {loading && !data && !isLanding ? (
        <LiteraryInlineLoader label="Собираем афишу Пушкиногорья…" compact />
      ) : isLanding && landingGarnectLoading && garnectProgram.length === 0 && displayPushkin.length === 0 ? (
        <LiteraryInlineLoader label="Собираем афишу Пушкиногорья…" compact />
      ) : showSplit ? (
        garnectProgram.length === 0 && displayPushkin.length === 0 ? (
          <LiteraryEmptyState {...EMPTY_STATES.events} compact={isLanding} />
        ) : (
          <>
            {garnectProgram.length > 0 && (
              <div className="events-festival-program-wrap mb-4">
                <FestivalProgramBlock
                  events={garnectProgram}
                  linkTo={isLanding ? garnectEventsPath() : undefined}
                  shareUrl={isLanding ? garnectShareUrl : undefined}
                />
              </div>
            )}
            {displayPushkin.length > 0 && (
              <ol
                className={[
                  "events-grid",
                  isLanding ? "events-grid--landing" : "events-grid--wide",
                  isLanding ? landingGridCountClass(displayPushkin.length, "events-grid--landing") : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                {displayPushkin.map((event) => (
                  <EventCard key={event.id} event={event} compact={isLanding} descLimit={isLanding ? 80 : 120} />
                ))}
              </ol>
            )}
          </>
        )
      ) : filteredEvents.length === 0 ? (
        <LiteraryEmptyState {...EMPTY_STATES.eventsSearch} />
      ) : (
        <ol className="events-grid events-grid--wide">
          {filteredEvents.map((event) => (
            <EventCard key={event.id} event={event} descLimit={120} spotlight={isRealCinemaEvent(event)} />
          ))}
        </ol>
      )}

      {isLanding && (
        <p className="landing-events-more m-0 mt-3">
          <Link to="/events" className="literary-link">🎬 Кино в Пскове</Link>
          <span className="landing-events-more-sep" aria-hidden> · </span>
          <Link to="/events?region=pskov" className="literary-link">События в городе</Link>
        </p>
      )}
    </section>
  );

  const cinemaBlock = displayCinema.length > 0 && (
    <CinemaSpotlight featured={isLanding} empty={isLanding && displayCinema.length === 0}>
      <ol
        className={[
          "events-grid",
          "events-grid--cinema",
          isLanding ? "events-grid--cinema-landing" : "",
          cinemaSingle ? "events-grid--cinema-single" : "",
          isLanding && displayCinema.length === 2 ? "events-grid--cinema-pair" : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {displayCinema.map((event, index) => (
          <EventCard
            key={event.id}
            event={event}
            descLimit={isLanding ? 90 : 100}
            spotlight
            className={
              isLanding && (index === 0 || cinemaSingle)
                ? "event-card-landing-featured"
                : isLanding && index === 1
                  ? "event-card-landing-secondary"
                  : ""
            }
          />
        ))}
      </ol>
    </CinemaSpotlight>
  );

  const pskovSection = displayPskov.length > 0 && (
    <section className="page-panel page-panel--gold landing-block events-city-pskov" aria-label="События в Пскове">
      <LiterarySectionHead
        kicker={pskovCopy.kicker}
        title={pskovCopy.title}
        lead={pskovCopy.lead}
        linkTo="/events?region=pskov"
        linkLabel="Афиша Пскова →"
      />
      <ol
        className={[
          "events-grid",
          isLanding ? "events-grid--landing-pskov" : "",
          isLanding ? landingGridCountClass(displayPskov.length, "events-grid--landing-pskov") : "",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {displayPskov.map((event) => (
          <EventCard key={event.id} event={event} descLimit={isLanding ? 90 : 100} />
        ))}
      </ol>
    </section>
  );

  return (
    <div className={isLanding ? "landing-events" : "literary-dashboard"}>
      {showCityRow && (
        <div className="events-city-row">
          {cinemaBlock}
          {pskovSection}
        </div>
      )}

      {isLanding ? (
        <>
          {pushkinSection}
          {pskovSection}
        </>
      ) : showCityRow ? (
        pushkinSection
      ) : (
        <>
          {pushkinSection}
          {cinemaBlock}
          {pskovSection}
        </>
      )}
    </div>
  );
}

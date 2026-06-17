import { FestivalProgramBlock, LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead, EventCard } from "@/components/literary";
import { EMPTY_STATES } from "@/lib/literaryCopy";

import { EventsCinemaBlock, EventsCityRow, EventsList, EventsPskovBlock } from "./EventsCityRow";
import type { EventsPageState } from "./useEventsPage";

type EventsDashboardProps = Pick<
  EventsPageState,
  | "EVENTS_COPY"
  | "cinemaEvents"
  | "garnectEventsPath"
  | "garnectOnly"
  | "garnectProgram"
  | "garnectShareUrl"
  | "loadError"
  | "loading"
  | "pskovEvents"
  | "pushkinOtherEvents"
  | "regionFilter"
  | "search"
  | "showCityRow"
  | "showGarnectOnlyBlock"
  | "showPushkinBlock"
  | "showPskovOnlyBlock"
  | "showSourceOnlyBlock"
  | "visibleEvents"
>;

export function EventsDashboard({
  EVENTS_COPY,
  cinemaEvents,
  garnectEventsPath,
  garnectOnly,
  garnectProgram,
  garnectShareUrl,
  loadError,
  loading,
  pskovEvents,
  pushkinOtherEvents,
  regionFilter,
  search,
  showCityRow,
  showGarnectOnlyBlock,
  showPushkinBlock,
  showPskovOnlyBlock,
  showSourceOnlyBlock,
  visibleEvents,
}: EventsDashboardProps) {
  if (loading) {
    return <LiteraryInlineLoader label="Собираем афишу Пушкиногорья…" />;
  }

  if (loadError) {
    return (
      <LiteraryEmptyState
        icon="⚠️"
        title="Афиша временно недоступна"
        text="Не удалось загрузить события. Попробуйте обновить страницу через минуту."
      />
    );
  }

  if (garnectOnly && garnectProgram.length === 0) {
    return (
      <LiteraryEmptyState
        {...(search
          ? EMPTY_STATES.eventsSearch
          : {
              icon: "🎭",
              title: "Программа пока не опубликована",
              text: "Следите за обновлениями афиши — спектакли фестиваля появятся здесь, как только источник их опубликует.",
            })}
      />
    );
  }

  if (visibleEvents.length === 0) {
    return <LiteraryEmptyState {...(search ? EMPTY_STATES.eventsSearch : EMPTY_STATES.events)} />;
  }

  return (
    <div className="literary-dashboard">
      {showCityRow && <EventsCityRow EVENTS_COPY={EVENTS_COPY} cinemaEvents={cinemaEvents} pskovEvents={pskovEvents} />}

      {regionFilter === "pskov" && !garnectOnly && <EventsCinemaBlock cinemaEvents={cinemaEvents} />}

      {showPskovOnlyBlock && <EventsPskovBlock EVENTS_COPY={EVENTS_COPY} pskovEvents={pskovEvents} cinemaEvents={cinemaEvents} />}

      {showSourceOnlyBlock && (
        <section className="page-panel page-panel--forest">
          <EventsList events={visibleEvents} />
        </section>
      )}

      {showGarnectOnlyBlock && (
        <section className="page-panel page-panel--forest">
          <div className="events-festival-program-wrap">
            <FestivalProgramBlock
              events={garnectProgram}
              shareUrl={garnectShareUrl}
              eventQuerySuffix="?from=garnect"
            />
          </div>
        </section>
      )}

      {showPushkinBlock && (
        <section className="page-panel page-panel--forest">
          <LiterarySectionHead kicker={EVENTS_COPY.pushkin.kicker} title={EVENTS_COPY.pushkin.title} compact />
          <ol className="events-grid events-grid--wide">
            {garnectProgram.length > 0 && (
              <li className="events-festival-program-wrap">
                <FestivalProgramBlock
                  events={garnectProgram}
                  linkTo={garnectEventsPath}
                  shareUrl={garnectShareUrl}
                  eventQuerySuffix="?from=garnect"
                />
              </li>
            )}
            {pushkinOtherEvents.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}

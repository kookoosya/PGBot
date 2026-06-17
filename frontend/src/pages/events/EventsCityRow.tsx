import { CinemaSpotlight, EventCard, LiteraryEmptyState, LiterarySectionHead } from "@/components/literary";
import type { PublicEvent } from "@/lib/api/types/events";
import { EMPTY_STATES } from "@/lib/literaryCopy";

import type { EventsPageState } from "./useEventsPage";

type EventsCityRowProps = Pick<EventsPageState, "EVENTS_COPY" | "cinemaEvents" | "pskovEvents">;

export function EventsCityRow({ EVENTS_COPY, cinemaEvents, pskovEvents }: EventsCityRowProps) {
  return (
    <div className="events-city-row">
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

      {pskovEvents.length > 0 && (
        <section className="page-panel page-panel--gold events-city-pskov">
          <LiterarySectionHead kicker={EVENTS_COPY.pskov.kicker} title={EVENTS_COPY.pskov.title} compact />
          <ol className="events-grid">
            {pskovEvents.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </ol>
        </section>
      )}
    </div>
  );
}

export function EventsPskovBlock({ EVENTS_COPY, pskovEvents }: EventsCityRowProps) {
  return (
    <section className="page-panel page-panel--gold events-city-pskov">
      <LiterarySectionHead kicker={EVENTS_COPY.pskov.kicker} title={EVENTS_COPY.pskov.title} compact />
      <ol className="events-grid">
        {pskovEvents.map((event) => (
          <EventCard key={event.id} event={event} />
        ))}
      </ol>
    </section>
  );
}

export function EventsCinemaBlock({ cinemaEvents }: Pick<EventsCityRowProps, "cinemaEvents">) {
  return (
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
}

type EventsListProps = {
  events: PublicEvent[];
  className?: string;
};

export function EventsList({ events, className = "events-grid events-grid--wide" }: EventsListProps) {
  return (
    <ol className={className}>
      {events.map((event) => (
        <EventCard key={event.id} event={event} />
      ))}
    </ol>
  );
}

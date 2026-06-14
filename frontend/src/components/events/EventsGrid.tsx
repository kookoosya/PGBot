import { EventCard } from "@/components/events/EventCard";
import {
  isCinemaEvent,
  type GroupedPublicEvent,
  type ShowGroupable,
} from "@/lib/eventUtils";
import type { PublicEvent, TodayEventSnippet } from "@/lib/api";

type GridEvent = PublicEvent | TodayEventSnippet | GroupedPublicEvent | ShowGroupable;

type EventsGridLayout = "auto" | "cinema" | "default";

interface EventsGridProps {
  events: GridEvent[];
  layout?: EventsGridLayout;
  landing?: boolean;
  emptyMessage?: string;
}

export function resolveEventsGridClass(
  events: GridEvent[],
  layout: EventsGridLayout = "auto",
  landing = false,
): string {
  const cinemaLayout =
    layout === "cinema" ||
    (layout === "auto" && events.length > 0 && events.every(isCinemaEvent));
  if (cinemaLayout) return "afisha-cinema-grid";
  return landing ? "afisha-grid afisha-grid--landing" : "afisha-grid";
}

export function EventsGrid({
  events,
  layout = "auto",
  landing = false,
  emptyMessage,
}: EventsGridProps) {
  if (!events.length) {
    return emptyMessage ? <p className="events-muted">{emptyMessage}</p> : null;
  }

  return (
    <div className={resolveEventsGridClass(events, layout, landing)}>
      {events.map((event) => (
        <EventCard
          key={event.id}
          event={event}
          variant={isCinemaEvent(event) ? "cinema" : landing ? "compact" : "grid"}
        />
      ))}
    </div>
  );
}

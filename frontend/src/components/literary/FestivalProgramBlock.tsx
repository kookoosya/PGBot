import { useMemo } from "react";
import type { PublicEvent } from "@/lib/api";
import { formatFestivalDateRange, pluralPerformances } from "@/lib/eventUtils";
import { EventCard } from "./EventCard";

interface FestivalProgramBlockProps {
  events: PublicEvent[];
  title?: string;
  kicker?: string;
}

export function FestivalProgramBlock({
  events,
  title = "Бугровский гарнец",
  kicker = "🎭 Фестиваль",
}: FestivalProgramBlockProps) {
  const dateRange = useMemo(() => formatFestivalDateRange(events), [events]);
  if (events.length < 2) return null;

  return (
    <details className="events-festival-program">
      <summary className="events-festival-program__summary">
        <div className="events-festival-program__head">
          <span className="events-festival-program__kicker">{kicker}</span>
          <span className="events-festival-program__title">{title}</span>
          <span className="events-festival-program__meta">
            {dateRange}
            {" · "}
            {events.length} {pluralPerformances(events.length)}
          </span>
        </div>
        <span className="events-festival-program__toggle" aria-hidden />
      </summary>
      <ol className="events-grid events-grid--festival">
        {events.map((event) => (
          <EventCard key={event.id} event={event} compact descLimit={90} />
        ))}
      </ol>
    </details>
  );
}

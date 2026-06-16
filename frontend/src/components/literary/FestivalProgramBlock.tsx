import { useMemo } from "react";
import { Link } from "react-router-dom";
import type { EventCardEvent } from "@/lib/eventUtils";
import { formatFestivalDateRange, pluralPerformances } from "@/lib/eventUtils";
import { EventCard } from "./EventCard";

interface FestivalProgramBlockProps {
  events: EventCardEvent[];
  title?: string;
  kicker?: string;
  linkTo?: string;
  linkLabel?: string;
}

export function FestivalProgramBlock({
  events,
  title = "Бугровский гарнец",
  kicker = "🎭 Фестиваль",
  linkTo,
  linkLabel = "Вся программа →",
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
          {linkTo && (
            <Link
              to={linkTo}
              className="events-festival-program__link"
              onClick={(event) => event.stopPropagation()}
            >
              {linkLabel}
            </Link>
          )}
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

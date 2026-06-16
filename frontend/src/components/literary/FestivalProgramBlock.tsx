import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { EventCardEvent } from "@/lib/eventUtils";
import { formatFestivalDateRange, FESTIVAL_COMPACT_LIST_THRESHOLD, isFestivalImminent, pluralPerformances } from "@/lib/eventUtils";
import { EventCard } from "./EventCard";
import { FestivalProgramSchedule } from "./FestivalProgramSchedule";

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
  const isImminent = useMemo(() => isFestivalImminent(events, 3), [events]);
  const [open, setOpen] = useState(isImminent);

  useEffect(() => {
    if (isImminent) setOpen(true);
  }, [isImminent]);

  if (events.length < 2) return null;

  const useCompactList = events.length >= FESTIVAL_COMPACT_LIST_THRESHOLD;

  return (
    <details
      className={`events-festival-program${isImminent ? " events-festival-program--imminent" : ""}`}
      open={open}
      onToggle={(event) => setOpen(event.currentTarget.open)}
    >
      <summary className="events-festival-program__summary">
        <div className="events-festival-program__head">
          <span className="events-festival-program__kicker">{kicker}</span>
          <span className="events-festival-program__title">
            {title}
            {isImminent && <span className="events-festival-program__badge">Скоро</span>}
          </span>
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
      {useCompactList ? (
        <div className="events-festival-program__body">
          <FestivalProgramSchedule events={events} />
        </div>
      ) : (
        <ol className="events-grid events-grid--festival">
          {events.map((event) => (
            <EventCard key={event.id} event={event} compact descLimit={90} />
          ))}
        </ol>
      )}
    </details>
  );
}

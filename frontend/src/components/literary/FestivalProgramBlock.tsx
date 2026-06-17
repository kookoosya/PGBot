import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import type { EventCardEvent } from "@/lib/eventUtils";
import { formatFestivalDateRange, FESTIVAL_COMPACT_LIST_THRESHOLD, festivalBadgeLabel, isFestivalImminent, pluralPerformances, sharePageUrl } from "@/lib/eventUtils";
import { GARNECT_FESTIVAL_TITLE } from "@/lib/festivalFilters";
import { EventCard } from "./EventCard";
import { FestivalProgramSchedule } from "./FestivalProgramSchedule";

interface FestivalProgramBlockProps {
  events: EventCardEvent[];
  title?: string;
  kicker?: string;
  linkTo?: string;
  linkLabel?: string;
  shareUrl?: string;
  eventQuerySuffix?: string;
}

export function FestivalProgramBlock({
  events,
  title = GARNECT_FESTIVAL_TITLE,
  kicker = "🎭 Фестиваль",
  linkTo,
  linkLabel = "Вся программа →",
  shareUrl,
  eventQuerySuffix,
}: FestivalProgramBlockProps) {
  const dateRange = useMemo(() => formatFestivalDateRange(events), [events]);
  const isImminent = useMemo(() => isFestivalImminent(events, 3), [events]);
  const badgeLabel = useMemo(() => festivalBadgeLabel(events), [events]);
  const [open, setOpen] = useState(isImminent);
  const [shareMsg, setShareMsg] = useState("");

  useEffect(() => {
    if (isImminent) setOpen(true);
  }, [isImminent]);

  const share = async (event: React.MouseEvent) => {
    event.stopPropagation();
    if (!shareUrl) return;
    const msg = await sharePageUrl(`${GARNECT_FESTIVAL_TITLE} — Пушкинские Горы`, shareUrl);
    if (msg) {
      setShareMsg(msg);
      window.setTimeout(() => setShareMsg(""), 2500);
    }
  };

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
            {badgeLabel && <span className="events-festival-program__badge">{badgeLabel}</span>}
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
          {shareUrl && (
            <button type="button" className="events-festival-program__link" onClick={share}>
              Поделиться
            </button>
          )}
        </div>
        <span className="events-festival-program__toggle" aria-hidden />
      </summary>
      {shareMsg && <p className="events-festival-program__share-msg">{shareMsg}</p>}
      {useCompactList ? (
        <div className="events-festival-program__body">
          <FestivalProgramSchedule events={events} eventQuerySuffix={eventQuerySuffix} />
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

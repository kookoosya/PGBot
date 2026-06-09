import { Link } from "react-router-dom";
import type { PublicEvent, TodayEventSnippet } from "@/lib/api";
import {
  categoryIcon,
  eventTeaser,
  formatExtraSessions,
  isCinemaEvent,
  isDisplayablePoster,
  regionChipClass,
  type GroupedPublicEvent,
} from "@/lib/eventUtils";

type EventCardVariant = "grid" | "cinema" | "compact";

type EventCardEvent = PublicEvent | TodayEventSnippet | GroupedPublicEvent;

interface EventCardProps {
  event: EventCardEvent;
  variant?: EventCardVariant;
}

export function EventCard({ event, variant = "grid" }: EventCardProps) {
  const cinema = isCinemaEvent(event);
  const cardClass = [
    "afisha-card",
    "literary-card",
    cinema ? "afisha-card--cinema literary-card--forest" : "literary-card--gold",
    variant === "cinema" ? "afisha-card--cinema-wide" : "",
    variant === "compact" ? "afisha-card--compact" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const rawPoster = "poster_url" in event ? event.poster_url : null;
  const posterUrl = isDisplayablePoster(rawPoster, event.category) ? rawPoster : null;
  const extraSessions =
    "extraSessions" in event && event.extraSessions?.length ? event.extraSessions : null;

  return (
    <article className={cardClass}>
      {posterUrl ? (
        <div
          className={[
            "afisha-card-poster",
            cinema ? "afisha-card-poster--cinema" : "afisha-card-poster--wide",
          ].join(" ")}
        >
          <img src={posterUrl} alt="" loading="lazy" decoding="async" />
        </div>
      ) : (
        <div
          className={[
            "afisha-card-poster",
            cinema ? "afisha-card-poster--cinema afisha-card-poster--placeholder" : "afisha-card-accent",
          ].join(" ")}
          aria-hidden={!cinema}
        >
          <span className="afisha-card-icon">{categoryIcon(event.category || "other")}</span>
        </div>
      )}

      <div className="afisha-card-body">
        <div className="afisha-card-meta">
          {event.region_label && (
            <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
          )}
          {event.category_label && (
            <span className="events-category">{event.category_label}</span>
          )}
          {event.genre && <span className="afisha-genre-chip">{event.genre}</span>}
        </div>

        <time
          className="afisha-card-date"
          dateTime={"starts_at" in event ? event.starts_at : undefined}
        >
          {event.starts_at_label}
          {event.ends_at_label && (
            <span className="events-date-end"> · до {event.ends_at_label}</span>
          )}
        </time>

        <h3 className="afisha-card-title">
          <Link to={`/events/${event.id}`} className="afisha-card-link">
            {event.title}
          </Link>
        </h3>

        {event.location && (
          <p className="afisha-card-location">📍 {event.location}</p>
        )}

        {event.description && (
          <p className="afisha-card-desc">{eventTeaser(event)}</p>
        )}

        {extraSessions && (
          <p className="afisha-card-sessions">{formatExtraSessions(extraSessions)}</p>
        )}

        <Link to={`/events/${event.id}`} className="afisha-card-cta">
          Подробнее →
        </Link>
      </div>
    </article>
  );
}

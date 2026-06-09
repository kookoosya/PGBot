import { Link } from "react-router-dom";
import type { PublicEvent, TodayEventSnippet } from "@/lib/api";
import { categoryIcon, eventTeaser, isCinemaEvent, regionChipClass } from "@/lib/eventUtils";

type EventCardVariant = "grid" | "cinema" | "compact";

type EventCardEvent = PublicEvent | TodayEventSnippet;

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

  const posterUrl = "poster_url" in event ? event.poster_url : null;

  return (
    <article className={cardClass}>
      {posterUrl ? (
        <div className="afisha-card-poster">
          <img src={posterUrl} alt="" loading="lazy" decoding="async" />
        </div>
      ) : (
        <div className="afisha-card-accent" aria-hidden>
          <span className="afisha-card-icon">{categoryIcon(event.category)}</span>
        </div>
      )}

      <div className="afisha-card-body">
        <div className="afisha-card-meta">
          <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
          <span className="events-category">{event.category_label}</span>
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

        <Link to={`/events/${event.id}`} className="afisha-card-cta">
          Подробнее →
        </Link>
      </div>
    </article>
  );
}

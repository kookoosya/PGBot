import { Link } from "react-router-dom";
import {
  eventTeaser,
  formatExtraSessions,
  isDisplayablePoster,
  isRealCinemaEvent,
  regionChipClass,
  type EventCardEvent,
  type GroupedPublicEvent,
} from "@/lib/eventUtils";

interface EventCardProps {
  event: EventCardEvent;
  descLimit?: number;
  showReadMore?: boolean;
  className?: string;
  /** Крупный кинематографичный вид внутри cinema-spotlight */
  spotlight?: boolean;
  /** Компактный вид на главной — без описания */
  compact?: boolean;
}

export function EventCard({
  event,
  descLimit = 140,
  showReadMore = true,
  className = "",
  spotlight = false,
  compact = false,
}: EventCardProps) {
  const cinema = isRealCinemaEvent(event);
  const isPskov = event.region_label === "Псков";
  const isPushkin = !isPskov;
  const posterUrl = isDisplayablePoster(
    "poster_url" in event ? event.poster_url : null,
    event.category,
  )
    ? (event as { poster_url?: string | null }).poster_url
    : null;
  const extraSessions = (event as GroupedPublicEvent).extraSessions;
  const teaser = compact ? "" : eventTeaser(event, descLimit);

  const cardClass = [
    "literary-card",
    cinema
      ? spotlight
        ? "literary-card--cinema-spotlight"
        : "literary-card--burgundy"
      : isPskov
        ? "literary-card--gold"
        : "literary-card--forest",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const innerClass = [
    "event-card",
    cinema ? "event-card--cinema" : "",
    cinema && spotlight ? "event-card--cinema-featured" : "",
    !cinema && isPskov ? "event-card--pskov" : "",
    !cinema && isPushkin ? "event-card--pushkin" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <li className={cardClass}>
      <Link to={`/events/${event.id}`} className={innerClass}>
        {cinema && (
          <div className="event-card-poster-wrap">
            {posterUrl ? (
              <div className="event-card-poster event-card-poster--image">
                <img src={posterUrl} alt="" loading="lazy" decoding="async" />
                {spotlight && <span className="event-card-poster-badge">Сеанс</span>}
              </div>
            ) : (
              <div className="event-card-poster" aria-hidden>
                <span className="event-card-poster-icon">🎬</span>
                {spotlight && <span className="event-card-poster-badge">Сеанс</span>}
              </div>
            )}
            <div className="event-card-film-strip" aria-hidden />
          </div>
        )}
        <div className={cinema ? "event-card-body" : "event-card-body event-card-body--stack"}>
          <div className="event-card-meta">
            <time className="event-card-date">{event.starts_at_label}</time>
            {event.ends_at_label && (
              <span className="events-date-end">до {event.ends_at_label}</span>
            )}
            <span className={regionChipClass(event.region_label || "Пушкинские Горы")}>{event.region_label}</span>
            {event.genre ? (
              <span className="events-category events-genre">{event.genre}</span>
            ) : (
              <span className="events-category">{event.category_label}</span>
            )}
          </div>
          <h3 className="event-card-title">{event.title}</h3>
          {event.location && <p className="event-card-location">📍 {event.location}</p>}
          {extraSessions && extraSessions.length > 0 && (
            <p className="event-card-sessions">{formatExtraSessions(extraSessions)}</p>
          )}
          {teaser && <p className="event-card-desc">{teaser}</p>}
          {showReadMore && (
            <span className="event-card-footer">
              {cinema ? "Билеты и подробности" : "Подробнее"}
              <span className="event-card-footer-arrow" aria-hidden> →</span>
            </span>
          )}
        </div>
      </Link>
    </li>
  );
}

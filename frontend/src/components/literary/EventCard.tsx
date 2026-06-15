import { Link } from "react-router-dom";
import { isCinemaEvent, regionChipClass } from "@/lib/eventUtils";

interface EventCardProps {
  event: {
    id: number;
    title: string;
    description?: string | null;
    starts_at_label: string;
    ends_at_label?: string | null;
    location?: string | null;
    region_label: string;
    category_label: string;
    category?: string;
  };
  descLimit?: number;
  showReadMore?: boolean;
  className?: string;
  /** Крупный кинематографичный вид внутри cinema-spotlight */
  spotlight?: boolean;
}

export function EventCard({
  event,
  descLimit = 140,
  showReadMore = true,
  className = "",
  spotlight = false,
}: EventCardProps) {
  const cinema = isCinemaEvent(event);
  const isPskov = event.region_label === "Псков";
  const isPushkin = !isPskov;
  const desc = event.description?.trim();
  const shortDesc =
    desc && desc.length > descLimit ? `${desc.slice(0, descLimit)}…` : desc;

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
            <div className="event-card-poster" aria-hidden>
              <span className="event-card-poster-icon">🎬</span>
              {spotlight && <span className="event-card-poster-badge">Сеанс</span>}
            </div>
            <div className="event-card-film-strip" aria-hidden />
          </div>
        )}
        <div className={cinema ? "event-card-body" : "event-card-body event-card-body--stack"}>
          <div className="event-card-meta">
            <time className="event-card-date">{event.starts_at_label}</time>
            {event.ends_at_label && (
              <span className="events-date-end">до {event.ends_at_label}</span>
            )}
            <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
            <span className="events-category">{event.category_label}</span>
          </div>
          <h3 className="event-card-title">{event.title}</h3>
          {event.location && <p className="event-card-location">📍 {event.location}</p>}
          {shortDesc && <p className="event-card-desc">{shortDesc}</p>}
          {showReadMore && (
            <span className="event-card-footer">
              {cinema ? "Билеты и подробности →" : "Подробнее →"}
            </span>
          )}
        </div>
      </Link>
    </li>
  );
}

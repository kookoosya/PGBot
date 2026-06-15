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
}

export function EventCard({
  event,
  descLimit = 140,
  showReadMore = true,
  className = "",
}: EventCardProps) {
  const cinema = isCinemaEvent(event);
  const isPskov = event.region_label === "Псков";
  const desc = event.description?.trim();
  const shortDesc =
    desc && desc.length > descLimit ? `${desc.slice(0, descLimit)}…` : desc;

  const cardClass = [
    "literary-card",
    cinema ? "literary-card--burgundy" : isPskov ? "literary-card--gold" : "literary-card--forest",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const innerClass = [
    "event-card",
    cinema ? "event-card--cinema" : "",
    cinema && isPskov ? "event-card--pskov" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <li className={cardClass}>
      <Link to={`/events/${event.id}`} className={innerClass}>
        {cinema && (
          <div className="event-card-poster" aria-hidden>
            🎬
          </div>
        )}
        <div className={cinema ? "event-card-body" : undefined}>
          <div className="event-card-meta">
            <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
            <span className="events-category">{event.category_label}</span>
            <time className="events-date">{event.starts_at_label}</time>
            {event.ends_at_label && (
              <span className="events-date-end">до {event.ends_at_label}</span>
            )}
          </div>
          <h3 className="event-card-title">{event.title}</h3>
          {event.location && <p className="event-card-location">📍 {event.location}</p>}
          {shortDesc && <p className="event-card-desc">{shortDesc}</p>}
          {showReadMore && <span className="event-card-footer">Подробнее →</span>}
        </div>
      </Link>
    </li>
  );
}

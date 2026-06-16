import { useEffect, useState } from "react";
import { LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { api, PublicEvent } from "@/lib/api";
import { eventSourceLabel, eventTeaser, isDisplayablePoster, isRealCinemaEvent, regionChipClass } from "@/lib/eventUtils";
import { LITERARY_VERSES } from "@/lib/literaryCopy";
import { VkBackBar } from "@/vk/components/VkBackBar";
import { VkErrorState } from "@/vk/components/VkErrorState";
import { useVkNavigation } from "@/vk/VkNavigationContext";
import { parseApiError } from "@/vk/lib/errors";

interface VkEventDetailProps {
  eventId: number;
}

export function VkEventDetail({ eventId }: VkEventDetailProps) {
  const { goBack } = useVkNavigation();
  const [event, setEvent] = useState<PublicEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    setError("");
    api
      .getPublicEvent(eventId)
      .then(setEvent)
      .catch((err) => {
        setEvent(null);
        setError(parseApiError(err));
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, [eventId]);

  if (loading) {
    return <LiteraryInlineLoader label="Загружаем событие…" compact />;
  }

  if (error || !event) {
    return (
      <section className="vk-tab-panel">
        <VkBackBar title="Событие" onBack={goBack} />
        <VkErrorState
          title="Событие недоступно"
          message={error || "Событие не найдено"}
          onRetry={load}
        />
      </section>
    );
  }

  const cinema = isRealCinemaEvent(event);
  const posterUrl = isDisplayablePoster(event.poster_url, event.category) ? event.poster_url : null;

  return (
    <section className="vk-tab-panel">
      <VkBackBar title="Событие" onBack={goBack} />

      <article className={`page-panel event-detail-panel ${cinema ? "page-panel--burgundy" : "page-panel--gold"}`}>
        {cinema && posterUrl && (
          <div className="event-card-poster event-card-poster--image event-detail-poster mb-3">
            <img src={posterUrl} alt="" loading="lazy" decoding="async" />
          </div>
        )}

        <h3 className="event-detail-title m-0 mb-2">{event.title}</h3>
        <div className="event-detail-meta mb-3">
          <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
          <span className="events-category">{event.category_label}</span>
        </div>

        <div className="event-detail-grid mb-3">
          <div>
            <p className="event-detail-label">Когда</p>
            <p className="event-detail-value m-0">
              <time>{event.starts_at_label}</time>
              {event.ends_at_label && <span> — до {event.ends_at_label}</span>}
            </p>
          </div>
          {event.location && (
            <div>
              <p className="event-detail-label">Где</p>
              <p className="event-detail-value m-0">📍 {event.location}</p>
            </div>
          )}
        </div>

        {event.description && (
          <div className="event-detail-desc">
            <LiterarySectionHead kicker="🪶 О событии" title="Подробности" />
            <p className="event-detail-text m-0">{cinema ? eventTeaser(event, 600) || event.description : event.description}</p>
          </div>
        )}

        <div className="event-detail-actions mt-4">
          {event.source_url ? (
            <a
              href={event.source_url}
              className="literary-btn literary-btn--primary no-underline w-full text-center"
              target="_blank"
              rel="noopener noreferrer"
            >
              Источник: {eventSourceLabel(event.source)}
            </a>
          ) : (
            <p className="text-sm text-muted-foreground m-0">Источник: {eventSourceLabel(event.source)}</p>
          )}
        </div>

        <p className="literary-page-verse event-detail-verse mt-4 mb-0" aria-hidden>
          {cinema ? LITERARY_VERSES.cinema : LITERARY_VERSES.events}
        </p>
      </article>
    </section>
  );
}

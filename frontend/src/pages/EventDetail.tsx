import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState, LiteraryInlineLoader, LiterarySectionHead } from "@/components/literary";
import { api, PublicEvent } from "@/lib/api";
import { CTA } from "@/lib/cta";
import { eventSourceLabel, eventTeaser, isDisplayablePoster, isRealCinemaEvent, regionChipClass, shareEventUrl } from "@/lib/eventUtils";
import { EMPTY_STATES } from "@/lib/literaryCopy";

export function EventDetail() {
  const { id } = useParams();
  const [event, setEvent] = useState<PublicEvent | null>(null);
  const [error, setError] = useState("");
  const [shareMsg, setShareMsg] = useState("");

  useEffect(() => {
    const num = Number(id);
    if (!num) {
      setError("Некорректный адрес события");
      return;
    }
    api.getPublicEvent(num)
      .then(setEvent)
      .catch(() => setError("Событие не найдено или снято с публикации"));
  }, [id]);

  const share = async () => {
    if (!event) return;
    const msg = await shareEventUrl(event.title);
    if (msg) {
      setShareMsg(msg);
      window.setTimeout(() => setShareMsg(""), 2500);
    }
  };

  if (error) {
    return (
      <div className="literary-page page-section max-w-3xl">
        <LiteraryEmptyState {...EMPTY_STATES.eventNotFound} text={error}>
          <Link to="/events" className="literary-btn literary-btn--ghost mt-2 no-underline">← К афише</Link>
        </LiteraryEmptyState>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="literary-page page-section max-w-3xl">
        <LiteraryInlineLoader label="Загружаем событие…" />
      </div>
    );
  }

  const cinema = isRealCinemaEvent(event);
  const posterUrl = isDisplayablePoster(event.poster_url, event.category) ? event.poster_url : null;

  return (
    <div className="literary-page page-section max-w-3xl">
      <PageHeader icon={cinema ? "🎬" : "📅"} title={event.title} subtitle={event.category_label}>
        <Link to="/events" className="literary-btn literary-btn--ghost text-sm no-underline">← {CTA.allEvents}</Link>
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={share}>
          Поделиться
        </button>
      </PageHeader>

      {shareMsg && <p className="alert-success mb-4">{shareMsg}</p>}

      <article className={`page-panel event-detail-panel ${cinema ? "page-panel--burgundy" : "page-panel--gold"}`}>
        {cinema && (
          <div className="event-detail-cinema-row">
            {posterUrl ? (
              <div className="event-card-poster event-card-poster--image event-detail-poster">
                <img src={posterUrl} alt="" loading="lazy" decoding="async" />
                <span className="event-card-poster-badge">Сеанс</span>
              </div>
            ) : (
              <div className="event-card-poster event-detail-poster" aria-hidden>
                <span className="event-card-poster-icon">🎬</span>
                <span className="event-card-poster-badge">Сеанс</span>
              </div>
            )}
            <div className="event-detail-meta">
              <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
              {event.genre ? (
                <span className="events-category events-genre">{event.genre}</span>
              ) : (
                <span className="events-category">{event.category_label}</span>
              )}
            </div>
          </div>
        )}

        {!cinema && (
          <div className="event-detail-meta mb-2">
            <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
            <span className="events-category">{event.category_label}</span>
            <span className="event-detail-source">Источник: {eventSourceLabel(event.source)}</span>
          </div>
        )}

        <div className="event-detail-grid">
          <div className="event-detail-when">
            <p className="event-detail-label">Когда</p>
            <p className="event-detail-value">
              <time>{event.starts_at_label}</time>
              {event.ends_at_label && <span className="event-detail-end"> — до {event.ends_at_label}</span>}
            </p>
          </div>

          {event.location && (
            <div className="event-detail-where">
              <p className="event-detail-label">Где</p>
              <p className="event-detail-value">📍 {event.location}</p>
            </div>
          )}
        </div>

        {event.description && (
          <div className="event-detail-desc">
            <LiterarySectionHead kicker="🪶 О событии" title="Подробности" />
            <p className="event-detail-text">{cinema ? eventTeaser(event, 600) || event.description : event.description}</p>
          </div>
        )}

        <div className="event-detail-actions">
          {event.source_url ? (
            <a
              href={event.source_url}
              className="literary-btn literary-btn--primary no-underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Перейти к источнику ({eventSourceLabel(event.source)})
            </a>
          ) : (
            <button type="button" className="literary-btn literary-btn--ghost" onClick={share}>
              Поделиться событием
            </button>
          )}
        </div>
      </article>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { LiteraryEmptyState } from "@/components/literary";
import { api, PublicEvent } from "@/lib/api";
import { eventSourceLabel, isCinemaEvent, regionChipClass, shareEventUrl } from "@/lib/eventUtils";

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
      <div className="page-section max-w-3xl">
        <LiteraryEmptyState icon="📅" title="Событие не найдено" text={error}>
          <Link to="/events" className="literary-btn literary-btn--ghost mt-2">← К афише</Link>
        </LiteraryEmptyState>
      </div>
    );
  }

  if (!event) {
    return <div className="page-section text-center text-muted-foreground py-16">Загружаем событие…</div>;
  }

  const cinema = isCinemaEvent(event);

  return (
    <div className="page-section max-w-3xl">
      <PageHeader icon={cinema ? "🎬" : "📅"} title={event.title} subtitle={event.category_label}>
        <Link to="/events" className="literary-btn literary-btn--ghost text-sm no-underline">← Вся афиша</Link>
        <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={share}>
          Поделиться
        </button>
      </PageHeader>

      {shareMsg && <p className="alert-success mb-4">{shareMsg}</p>}

      <article className={`event-detail-card literary-card ${cinema ? "literary-card--burgundy" : "literary-card--gold"}`}>
        {cinema && (
          <div className="event-card--cinema mb-4" style={{ display: "grid", gridTemplateColumns: "5.5rem 1fr", gap: "1rem" }}>
            <div className="event-card-poster" aria-hidden>🎬</div>
            <div className="event-card-body">
              <div className="event-detail-meta">
                <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
                <span className="events-category">{event.category_label}</span>
              </div>
            </div>
          </div>
        )}

        {!cinema && (
          <div className="event-detail-meta">
            <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
            <span className="events-category">{event.category_label}</span>
            <span className="event-detail-source">Источник: {eventSourceLabel(event.source)}</span>
          </div>
        )}

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

        {event.description && (
          <div className="event-detail-desc">
            <p className="event-detail-label">О событии</p>
            <p className="event-detail-text">{event.description}</p>
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

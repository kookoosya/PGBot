import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { api, PublicEventDetail } from "@/lib/api";
import {
  categoryIcon,
  eventSourceLabel,
  isCinemaEvent,
  regionChipClass,
  shareEventUrl,
} from "@/lib/eventUtils";

export function EventDetail() {
  const { id } = useParams();
  const [event, setEvent] = useState<PublicEventDetail | null>(null);
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
      <div className="page-section max-w-3xl text-center py-16">
        <p className="text-muted-foreground mb-4">{error}</p>
        <Link to="/events" className="btn-hero-secondary inline-flex no-underline">← К афише</Link>
      </div>
    );
  }

  if (!event) {
    return <div className="page-section text-center text-muted-foreground py-16">Загружаем событие…</div>;
  }

  const cinema = isCinemaEvent(event);

  return (
    <div className="afisha-detail page-section max-w-3xl">
      <nav className="afisha-breadcrumb" aria-label="Навигация">
        <Link to="/">Главная</Link>
        <span aria-hidden> / </span>
        <Link to="/events">Афиша</Link>
        <span aria-hidden> / </span>
        <span className="afisha-breadcrumb-current">{event.title.slice(0, 40)}{event.title.length > 40 ? "…" : ""}</span>
      </nav>

      <article className={`afisha-detail-card literary-card ${cinema ? "literary-card--forest afisha-detail-card--cinema" : "literary-card--gold"}`}>
        {event.poster_url && (
          <div className="afisha-detail-poster">
            <img src={event.poster_url} alt={`Постер: ${event.title}`} loading="eager" decoding="async" />
          </div>
        )}
        <div className="afisha-detail-hero">
          <span className="afisha-detail-icon" aria-hidden>{categoryIcon(event.category)}</span>
          <div className="afisha-detail-hero-copy">
            <div className="afisha-card-meta">
              <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
              <span className="events-category">{event.category_label}</span>
              {event.genre && <span className="afisha-genre-chip">{event.genre}</span>}
            </div>
            <h1 className="afisha-detail-title">{event.title}</h1>
            {cinema && event.genre && (
              <p className="afisha-detail-genre-line">Жанр: {event.genre}</p>
            )}
          </div>
        </div>

        <div className="afisha-detail-facts">
          <div className="afisha-fact">
            <p className="event-detail-label">Когда</p>
            <p className="event-detail-value">
              <time dateTime={event.starts_at}>{event.starts_at_label}</time>
              {event.ends_at_label && (
                <span className="event-detail-end"> — до {event.ends_at_label}</span>
              )}
            </p>
          </div>

          {event.location && (
            <div className="afisha-fact">
              <p className="event-detail-label">Где</p>
              <p className="event-detail-value">📍 {event.location}</p>
            </div>
          )}
        </div>

        {event.description && (
          <div className="afisha-detail-desc">
            <p className="event-detail-label">{cinema ? "О фильме" : "О событии"}</p>
            <p className="event-detail-text">{event.description}</p>
          </div>
        )}

        {event.related_sessions?.length > 0 && (
          <div className="afisha-detail-sessions">
            <p className="event-detail-label">Другие сеансы</p>
            <ul className="afisha-session-list">
              {event.related_sessions.map((session) => (
                <li key={session.id}>
                  <Link to={`/events/${session.id}`}>
                    {session.starts_at_label}
                    {session.ends_at_label ? ` · до ${session.ends_at_label}` : ""}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="afisha-detail-source">Источник: {eventSourceLabel(event.source)}</p>

        {shareMsg && <p className="alert-success">{shareMsg}</p>}

        <div className="afisha-detail-actions">
          {event.source_url ? (
            <a
              href={event.source_url}
              className="btn-hero-primary no-underline inline-flex"
              target="_blank"
              rel="noopener noreferrer"
            >
              {cinema ? "Билеты / расписание" : `Перейти к источнику (${eventSourceLabel(event.source)})`}
            </a>
          ) : null}
          <Button type="button" variant="outline" onClick={share}>Поделиться</Button>
          <Link to="/events" className="btn-hero-secondary no-underline inline-flex">← Вся афиша</Link>
        </div>
      </article>
    </div>
  );
}

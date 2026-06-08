import { useToday } from "@/hooks/useToday";

export function UpcomingEvents() {
  const { data, loading } = useToday();
  const events = data?.upcoming_events ?? [];

  return (
    <section className="events-panel" aria-label="Ближайшие события">
      <div className="events-panel-head">
        <div>
          <p className="events-kicker">📅 Афиша посёлка</p>
          <h2>Ближайшие события</h2>
        </div>
      </div>

      {loading && !data ? (
        <p className="events-muted">Загружаем афишу…</p>
      ) : events.length === 0 ? (
        <p className="events-muted">
          Скоро здесь появятся концерты, праздники и встречи — следите за обновлениями.
        </p>
      ) : (
        <ol className="events-list">
          {events.map((event) => (
            <li key={event.id} className="events-item">
              <div className="events-item-meta">
                <span className="events-category">{event.category_label}</span>
                <time className="events-date">{event.starts_at_label}</time>
                {event.ends_at_label && (
                  <span className="events-date-end">до {event.ends_at_label}</span>
                )}
              </div>
              {event.source_url ? (
                <a
                  href={event.source_url}
                  className="events-title events-title-link"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {event.title}
                </a>
              ) : (
                <p className="events-title">{event.title}</p>
              )}
              {event.location && <p className="events-location">📍 {event.location}</p>}
              {event.description && <p className="events-desc">{event.description}</p>}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

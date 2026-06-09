import { useMemo } from "react";
import { Link } from "react-router-dom";
import { EventsGrid } from "@/components/events/EventsGrid";
import { useToday } from "@/hooks/useToday";
import { groupEventsByShow, isCinemaEvent } from "@/lib/eventUtils";

export function UpcomingEvents() {
  const { data, loading } = useToday();
  const events = data?.upcoming_events ?? [];

  const { cinemaPreview, otherPreview } = useMemo(() => {
    const grouped = groupEventsByShow(events);
    return {
      cinemaPreview: grouped.filter(isCinemaEvent).slice(0, 4),
      otherPreview: grouped.filter((e) => !isCinemaEvent(e)).slice(0, 4),
    };
  }, [events]);

  const hasEvents = cinemaPreview.length > 0 || otherPreview.length > 0;

  return (
    <section className="events-panel" aria-label="Ближайшие события">
      <div className="events-panel-head">
        <div>
          <p className="events-kicker">📅 Афиша региона</p>
          <h2>Ближайшие события</h2>
          <p className="events-lead">
            Кино в Пскове и события в Пушкинских Горах — краткая подборка. Полное расписание на странице афиши.
          </p>
        </div>
        <Link to="/events" className="events-all-link">Вся афиша →</Link>
      </div>

      {loading && !data ? (
        <p className="events-muted">Загружаем афишу…</p>
      ) : !hasEvents ? (
        <p className="events-muted">Скоро здесь появятся события — откройте всю афишу.</p>
      ) : (
        <div className="landing-events-preview">
          {cinemaPreview.length > 0 && (
            <div className="landing-events-block">
              <div className="landing-events-block-head">
                <h3>🎬 Кино в Пскове</h3>
                <Link to="/events?category=cinema" className="landing-events-block-link">
                  Все сеансы →
                </Link>
              </div>
              <EventsGrid events={cinemaPreview} layout="cinema" landing />
            </div>
          )}

          {otherPreview.length > 0 && (
            <div className="landing-events-block">
              <div className="landing-events-block-head">
                <h3>🏛 События региона</h3>
                <Link to="/events" className="landing-events-block-link">
                  Вся афиша →
                </Link>
              </div>
              <EventsGrid events={otherPreview} layout="default" landing />
            </div>
          )}
        </div>
      )}
    </section>
  );
}

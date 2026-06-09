import { useMemo } from "react";
import { Link } from "react-router-dom";
import { EventsGrid } from "@/components/events/EventsGrid";
import { useToday } from "@/hooks/useToday";
import { groupEventsByShow, isCinemaEvent } from "@/lib/eventUtils";

function showKey(event: { title: string; location?: string | null; region: string }): string {
  return `${event.title}|${event.location || ""}|${event.region}`;
}

export function UpcomingEvents() {
  const { data, loading } = useToday();
  const events = data?.upcoming_events ?? [];

  const { pushkinPreview, cinemaPreview } = useMemo(() => {
    const grouped = groupEventsByShow(events);
    const pushkin = grouped
      .filter((e) => e.region === "pushkin_gory")
      .slice(0, 4);
    const usedKeys = new Set(pushkin.map(showKey));
    const cinema = grouped
      .filter((e) => isCinemaEvent(e) && e.region === "pskov" && !usedKeys.has(showKey(e)))
      .slice(0, 2);
    return { pushkinPreview: pushkin, cinemaPreview: cinema };
  }, [events]);

  const hasEvents = pushkinPreview.length > 0 || cinemaPreview.length > 0;

  return (
    <section className="events-panel" aria-label="Ближайшие события">
      <div className="events-panel-head">
        <div>
          <p className="events-kicker">📅 Афиша посёлка</p>
          <h2>Ближайшие события</h2>
          <p className="events-lead">
            Сначала — Пушкинские Горы. Ниже — кратко кино в Пскове для гостей региона.
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
          {pushkinPreview.length > 0 && (
            <div className="landing-events-block">
              <div className="landing-events-block-head">
                <h3>🏛 Пушкинские Горы</h3>
                <Link to="/events?region=pushkin_gory" className="landing-events-block-link">
                  Все события →
                </Link>
              </div>
              <EventsGrid events={pushkinPreview} layout="default" landing />
            </div>
          )}

          {cinemaPreview.length > 0 && (
            <div className="landing-events-block landing-events-block--cinema">
              <div className="landing-events-block-head">
                <h3>🎬 Кино в Пскове</h3>
                <Link to="/events?category=cinema&region=pskov" className="landing-events-block-link">
                  Все сеансы →
                </Link>
              </div>
              <EventsGrid events={cinemaPreview} layout="cinema" landing landingCinemaStrip />
            </div>
          )}
        </div>
      )}
    </section>
  );
}

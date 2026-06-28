import { Link } from "react-router-dom";
import { LiterarySectionHead, LiteraryInlineLoader } from "@/components/literary";
import { LandingCard } from "@/components/landing/LandingCard";
import { formatTodayUpdatedAt, useToday } from "@/hooks/useToday";
import { EMPTY_STATES, LANDING_SECTIONS } from "@/lib/literaryCopy";

const copy = LANDING_SECTIONS.today;

export function TodayInVillage() {
  const { data, loading, error } = useToday();

  if (loading && !data) {
    return (
      <section className="page-panel page-panel--gold landing-block landing-today-panel" aria-busy="true">
        <LiterarySectionHead title={copy.title} compact />
        <LiteraryInlineLoader label="Собираем сводку дня…" compact />
      </section>
    );
  }

  if (error && !data) {
    return (
      <section className="page-panel page-panel--gold landing-block landing-today-panel">
        <LiterarySectionHead title={copy.title} compact />
        <p className="landing-muted">Сводка дня временно недоступна — загляните чуть позже.</p>
      </section>
    );
  }

  if (!data) return null;

  const ad = data.latest_classified;
  const nextEvent = data.upcoming_events[0] ?? null;

  return (
    <section className="page-panel page-panel--gold landing-block landing-today-panel" aria-label="Сегодня в посёлке">
      <LiterarySectionHead
        title={copy.title}
        lead={copy.lead}
        meta={<p className="landing-updated">Обновлено {formatTodayUpdatedAt(data.updated_at)}</p>}
      />

      <div className="landing-today-grid">
        <LandingCard
          title="Ближайшее событие"
          action={{ label: "Вся афиша →", to: "/events" }}
          className="landing-card--event"
        >
          {nextEvent ? (
            <>
              <p className="landing-card-meta">{nextEvent.starts_at_label}</p>
              <Link to={`/events/${nextEvent.id}`} className="landing-card-link">
                {nextEvent.title}
              </Link>
              {nextEvent.location && <p className="landing-card-date">{nextEvent.location}</p>}
            </>
          ) : (
            <p className="landing-muted m-0">
              {EMPTY_STATES.events.title}.{" "}
              <Link to="/events" className="literary-link">
                Афиша →
              </Link>
            </p>
          )}
        </LandingCard>

        <LandingCard
          title="Свежее объявление"
          action={{ label: "Все объявления →", to: "/classifieds" }}
          className="landing-card--ad"
        >
          {ad ? (
            <>
              <p className="landing-card-meta">{ad.category_label}</p>
              <Link to={`/classifieds/${ad.id}`} className="landing-card-link">
                {ad.title}
              </Link>
            </>
          ) : (
            <p className="landing-muted m-0">
              {EMPTY_STATES.todayNoAd.text}{" "}
              <Link to="/classifieds?new=1" className="literary-link">
                Подать →
              </Link>
            </p>
          )}
        </LandingCard>

        <LandingCard
          title="Справочник на карте"
          action={{ label: "Открыть карту →", to: "/map" }}
          className="landing-card--map"
        >
          <dl className="landing-stat-grid">
            <div>
              <dt>Организаций</dt>
              <dd>{data.map.total_places}</dd>
            </div>
            <div>
              <dt>Отзывов</dt>
              <dd>{data.map.total_reviews}</dd>
            </div>
            <div>
              <dt>Такси</dt>
              <dd>{data.map.active_taxi_count}</dd>
            </div>
            <div>
              <dt>Маршрутов</dt>
              <dd>{data.map.route_count}</dd>
            </div>
          </dl>
        </LandingCard>
      </div>
    </section>
  );
}

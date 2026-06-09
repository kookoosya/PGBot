import { useMemo, useState } from "react";
import { type EventRegion } from "@/lib/api";
import { useToday } from "@/hooks/useToday";

type RegionFilter = "all" | EventRegion;

const REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

function regionChipClass(regionLabel: string): string {
  if (regionLabel === "Псков") return "events-region-chip events-region-chip--pskov";
  return "events-region-chip events-region-chip--pushkin";
}

export function UpcomingEvents() {
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const apiRegion = regionFilter === "all" ? undefined : regionFilter;
  const { data, loading } = useToday(apiRegion);
  const events = data?.upcoming_events ?? [];

  const visibleEvents = useMemo(() => {
    if (regionFilter === "all") return events;
    const label = regionFilter === "pskov" ? "Псков" : "Пушкинские Горы";
    return events.filter((event) => event.region_label === label);
  }, [events, regionFilter]);

  return (
    <section className="events-panel" aria-label="Ближайшие события">
      <div className="events-panel-head">
        <div>
          <p className="events-kicker">📅 Афиша региона</p>
          <h2>Ближайшие события</h2>
          <p className="events-lead">
            Концерты и праздники в Пушкинских Горах, кино и мероприятия в Пскове — для жителей и гостей.
          </p>
        </div>
      </div>

      <div className="events-region-filters" role="group" aria-label="Фильтр по региону">
        {REGION_FILTERS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`events-region-filter${regionFilter === item.id ? " events-region-filter--active" : ""}`}
            onClick={() => setRegionFilter(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {loading && !data ? (
        <p className="events-muted">Загружаем афишу…</p>
      ) : visibleEvents.length === 0 ? (
        <p className="events-muted">
          {regionFilter === "all"
            ? "Скоро здесь появятся концерты, ярмарки и встречи в музее-заповеднике и Пскове — следите за обновлениями."
            : "В этом регионе пока нет ближайших событий — попробуйте другой фильтр или загляните позже."}
        </p>
      ) : (
        <ol className="events-list">
          {visibleEvents.map((event) => (
            <li key={event.id} className="events-item">
              <div className="events-item-meta">
                <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
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

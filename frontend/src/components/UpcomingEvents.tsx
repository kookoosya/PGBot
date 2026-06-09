import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { type EventRegion } from "@/lib/api";
import { regionChipClass } from "@/lib/eventUtils";
import { useToday } from "@/hooks/useToday";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

type RegionFilter = "all" | EventRegion;

const REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

export function UpcomingEvents() {
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const apiRegion = regionFilter === "all" ? undefined : regionFilter;
  const { data, loading } = useToday(apiRegion);
  const events = data?.upcoming_events ?? [];

  const visibleEvents = useMemo(() => {
    let list = events;
    if (regionFilter !== "all") {
      const label = regionFilter === "pskov" ? "Псков" : "Пушкинские Горы";
      list = list.filter((event) => event.region_label === label);
    }
    const q = searchInput.trim().toLowerCase();
    if (q) {
      list = list.filter(
        (e) =>
          e.title.toLowerCase().includes(q) ||
          (e.description?.toLowerCase().includes(q) ?? false) ||
          e.category_label.toLowerCase().includes(q),
      );
    }
    return list;
  }, [events, regionFilter, searchInput]);

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
        <Link to="/events" className="events-all-link">Вся афиша →</Link>
      </div>

      <div className="events-toolbar">
        <div className="events-region-filters events-region-filters--inline" role="group" aria-label="Фильтр по региону">
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
        <div className="events-search-row">
          <Input
            placeholder="Поиск…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="events-search-input"
          />
          {searchInput && (
            <Button type="button" variant="outline" size="sm" onClick={() => setSearchInput("")}>
              Сброс
            </Button>
          )}
        </div>
      </div>

      {loading && !data ? (
        <p className="events-muted">Загружаем афишу…</p>
      ) : visibleEvents.length === 0 ? (
        <p className="events-muted">
          {searchInput
            ? "Ничего не найдено — попробуйте другой запрос."
            : regionFilter === "all"
              ? "Скоро здесь появятся концерты, ярмарки и встречи — следите за обновлениями или откройте всю афишу."
              : "В этом регионе пока нет ближайших событий."}
        </p>
      ) : (
        <ol className="events-list">
          {visibleEvents.map((event) => (
            <li key={event.id} className="events-item literary-card literary-card--gold">
              <div className="events-item-meta">
                <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
                <span className="events-category">{event.category_label}</span>
                <time className="events-date">{event.starts_at_label}</time>
                {event.ends_at_label && (
                  <span className="events-date-end">до {event.ends_at_label}</span>
                )}
              </div>
              <Link to={`/events/${event.id}`} className="events-title events-title-link">
                {event.title}
              </Link>
              {event.location && <p className="events-location">📍 {event.location}</p>}
              {event.description && <p className="events-desc">{event.description.slice(0, 120)}{event.description.length > 120 ? "…" : ""}</p>}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

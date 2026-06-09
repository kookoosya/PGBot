import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { EventCard } from "@/components/events/EventCard";
import { type EventRegion } from "@/lib/api";
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
          (e.genre?.toLowerCase().includes(q) ?? false) ||
          e.category_label.toLowerCase().includes(q),
      );
    }
    return list.slice(0, 6);
  }, [events, regionFilter, searchInput]);

  return (
    <section className="events-panel" aria-label="Ближайшие события">
      <div className="events-panel-head">
        <div>
          <p className="events-kicker">📅 Афиша региона</p>
          <h2>Ближайшие события</h2>
          <p className="events-lead">
            Экскурсии и праздники в Пушкинских Горах, кино и концерты в Пскове.
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
            : "Скоро здесь появятся события — откройте всю афишу."}
        </p>
      ) : (
        <div className="afisha-grid afisha-grid--landing">
          {visibleEvents.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              variant={event.category === "cinema" ? "cinema" : "compact"}
            />
          ))}
        </div>
      )}
    </section>
  );
}

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "@/components/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, EventRegion, PublicEvent } from "@/lib/api";
import { regionChipClass } from "@/lib/eventUtils";

type RegionFilter = "all" | EventRegion;

const REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

export function EventsPage() {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    api
      .getPublicEvents({
        region: regionFilter === "all" ? undefined : regionFilter,
        search: search || undefined,
        limit: "40",
      })
      .then((r) => setEvents(r.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [regionFilter, search]);

  const categoryFilters = useMemo(() => {
    const cats = new Set(events.map((e) => e.category_label));
    return Array.from(cats).sort();
  }, [events]);

  const [categoryFilter, setCategoryFilter] = useState("");

  const visibleEvents = useMemo(() => {
    if (!categoryFilter) return events;
    return events.filter((e) => e.category_label === categoryFilter);
  }, [events, categoryFilter]);

  return (
    <div className="page-section max-w-5xl">
      <PageHeader
        icon="📅"
        title="Афиша региона"
        subtitle="Концерты, праздники и кино в Пушкинских Горах и Пскове"
      />

      <div className="page-panel page-panel--forest mb-6">
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <Input
            placeholder="Поиск: концерт, кино, ярмарка…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="flex-1"
          />
          <Button type="button" variant="outline" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </Button>
        </div>

        <div className="events-region-filters mb-0" role="group" aria-label="Регион">
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

        {categoryFilters.length > 1 && (
          <div className="filter-bar mt-4">
            <button
              type="button"
              className={`filter-chip${!categoryFilter ? " filter-chip-active" : ""}`}
              onClick={() => setCategoryFilter("")}
            >
              Все категории
            </button>
            {categoryFilters.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`filter-chip${categoryFilter === cat ? " filter-chip-active" : ""}`}
                onClick={() => setCategoryFilter(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        )}
      </div>

      {loading ? (
        <p className="events-muted">Загружаем афишу…</p>
      ) : visibleEvents.length === 0 ? (
        <p className="events-muted">Событий не найдено — попробуйте другой фильтр или загляните позже.</p>
      ) : (
        <ol className="events-list">
          {visibleEvents.map((event) => (
            <li key={event.id} className="events-item literary-card literary-card--gold">
              <div className="events-item-meta">
                <span className={regionChipClass(event.region_label)}>{event.region_label}</span>
                <span className="events-category">{event.category_label}</span>
                <time className="events-date">{event.starts_at_label}</time>
              </div>
              <Link to={`/events/${event.id}`} className="events-title events-title-link">
                {event.title}
              </Link>
              {event.location && <p className="events-location">📍 {event.location}</p>}
              {event.description && <p className="events-desc">{event.description.slice(0, 160)}{event.description.length > 160 ? "…" : ""}</p>}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

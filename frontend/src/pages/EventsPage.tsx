import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { EventsGrid } from "@/components/events/EventsGrid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, EventRegion, PublicEvent } from "@/lib/api";
import { groupEventsByShow, isCinemaEvent } from "@/lib/eventUtils";

type RegionFilter = "all" | EventRegion;
type CategoryFilter = "all" | string;

const REGION_FILTERS: { id: RegionFilter; label: string }[] = [
  { id: "all", label: "Все регионы" },
  { id: "pushkin_gory", label: "Пушкинские Горы" },
  { id: "pskov", label: "Псков" },
];

const CATEGORY_TABS: { id: CategoryFilter; label: string; icon: string }[] = [
  { id: "all", label: "Всё", icon: "📅" },
  { id: "cinema", label: "Кино", icon: "🎬" },
  { id: "culture", label: "Культура", icon: "🎭" },
  { id: "holiday", label: "Праздники", icon: "🎉" },
  { id: "tourism", label: "Туризм", icon: "🧭" },
];

function filterByRegion<T extends { region: EventRegion }>(
  events: T[],
  region: RegionFilter,
): T[] {
  if (region === "all") return events;
  return events.filter((event) => event.region === region);
}

export function EventsPage() {
  const [searchParams] = useSearchParams();
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    const category = searchParams.get("category");
    if (category && CATEGORY_TABS.some((tab) => tab.id === category)) {
      setCategoryFilter(category);
    }
    const region = searchParams.get("region");
    if (region && REGION_FILTERS.some((item) => item.id === region)) {
      setRegionFilter(region as RegionFilter);
    }
  }, [searchParams]);

  useEffect(() => {
    setLoading(true);
    const limit = categoryFilter === "cinema" ? "80" : "60";
    api
      .getPublicEvents({
        region: regionFilter === "all" ? undefined : regionFilter,
        category: categoryFilter === "all" ? undefined : categoryFilter,
        search: search || undefined,
        limit,
      })
      .then((r) => setEvents(r.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [regionFilter, categoryFilter, search]);

  const groupedEvents = useMemo(() => groupEventsByShow(events), [events]);

  const showSections = categoryFilter === "all" && !search;

  const cinemaPskov = useMemo(
    () =>
      filterByRegion(
        groupedEvents.filter((e) => isCinemaEvent(e) && e.region === "pskov"),
        regionFilter,
      ),
    [groupedEvents, regionFilter],
  );

  const pushkinEvents = useMemo(
    () =>
      filterByRegion(
        groupedEvents.filter((e) => e.region === "pushkin_gory" && !isCinemaEvent(e)),
        regionFilter,
      ),
    [groupedEvents, regionFilter],
  );

  const pskovOther = useMemo(
    () =>
      filterByRegion(
        groupedEvents.filter((e) => e.region === "pskov" && !isCinemaEvent(e)),
        regionFilter,
      ),
    [groupedEvents, regionFilter],
  );

  const flatLayout = categoryFilter === "cinema" ? "cinema" : "auto";

  return (
    <div className="afisha-page page-section max-w-6xl">
      <nav className="afisha-breadcrumb" aria-label="Навигация">
        <Link to="/">Главная</Link>
        <span aria-hidden> / </span>
        <span>Афиша</span>
      </nav>

      <header className="afisha-hero">
        <p className="afisha-kicker">🪶 Литературный альбом · Афиша</p>
        <h1 className="afisha-title">События региона</h1>
        <p className="afisha-lead">
          Для жителей Пушкинских Гор и гостей: экскурсии, концерты, ярмарки и киноафиша Пскова —
          в одном месте.
        </p>
      </header>

      <div className="afisha-filters literary-card literary-card--forest">
        <div className="afisha-search-row">
          <Input
            placeholder="Поиск: фильм, концерт, экскурсия…"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && setSearch(searchInput.trim())}
            className="afisha-search-input"
          />
          <Button type="button" variant="outline" onClick={() => setSearch(searchInput.trim())}>
            Найти
          </Button>
          {search && (
            <Button type="button" variant="ghost" onClick={() => { setSearch(""); setSearchInput(""); }}>
              Сброс
            </Button>
          )}
        </div>

        <div className="afisha-filter-groups">
          <div className="events-region-filters" role="group" aria-label="Регион">
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

          <div className="afisha-category-tabs" role="tablist" aria-label="Категория">
            {CATEGORY_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={categoryFilter === tab.id}
                className={`afisha-category-tab${categoryFilter === tab.id ? " afisha-category-tab--active" : ""}`}
                onClick={() => setCategoryFilter(tab.id)}
              >
                <span aria-hidden>{tab.icon}</span> {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <p className="events-muted afisha-loading">Загружаем афишу…</p>
      ) : events.length === 0 ? (
        <p className="events-muted">Событий не найдено — попробуйте другой фильтр.</p>
      ) : showSections ? (
        <div className="afisha-sections">
          {cinemaPskov.length > 0 && (
            <section className="afisha-section" aria-labelledby="cinema-heading">
              <div className="afisha-section-head">
                <h2 id="cinema-heading">🎬 Кино в Пскове</h2>
                <p className="afisha-section-lead">
                  Победа, Смена, Мираж Синема, Silver Cinema — сеансы с постерами и жанрами.
                </p>
              </div>
              <EventsGrid events={cinemaPskov} layout="cinema" />
            </section>
          )}

          {pushkinEvents.length > 0 && (
            <section className="afisha-section" aria-labelledby="pg-heading">
              <div className="afisha-section-head">
                <h2 id="pg-heading">🏛 Пушкинские Горы</h2>
                <p className="afisha-section-lead">Музей-заповедник, экскурсии и праздники для туристов и жителей.</p>
              </div>
              <EventsGrid events={pushkinEvents} layout="default" />
            </section>
          )}

          {pskovOther.length > 0 && (
            <section className="afisha-section" aria-labelledby="pskov-heading">
              <div className="afisha-section-head">
                <h2 id="pskov-heading">🏰 Псков</h2>
                <p className="afisha-section-lead">Концерты, выставки и городские мероприятия.</p>
              </div>
              <EventsGrid events={pskovOther} layout="default" />
            </section>
          )}
        </div>
      ) : (
        <EventsGrid events={groupedEvents} layout={flatLayout} />
      )}
    </div>
  );
}

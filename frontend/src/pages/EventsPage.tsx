import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { EventCard } from "@/components/events/EventCard";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, EventRegion, PublicEvent } from "@/lib/api";
import { isCinemaEvent } from "@/lib/eventUtils";

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

export function EventsPage() {
  const [events, setEvents] = useState<PublicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [regionFilter, setRegionFilter] = useState<RegionFilter>("all");
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    setLoading(true);
    api
      .getPublicEvents({
        region: regionFilter === "all" ? undefined : regionFilter,
        category: categoryFilter === "all" ? undefined : categoryFilter,
        search: search || undefined,
        limit: "60",
      })
      .then((r) => setEvents(r.items))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [regionFilter, categoryFilter, search]);

  const cinemaPskov = useMemo(
    () => events.filter((e) => isCinemaEvent(e) && e.region === "pskov"),
    [events],
  );

  const pushkinEvents = useMemo(
    () => events.filter((e) => e.region === "pushkin_gory" && !isCinemaEvent(e)),
    [events],
  );

  const pskovOther = useMemo(
    () => events.filter((e) => e.region === "pskov" && !isCinemaEvent(e)),
    [events],
  );

  const showSections =
    categoryFilter === "all" && !search && regionFilter === "all";

  const flatList = useMemo(() => {
    if (showSections) return [];
    return events;
  }, [events, showSections]);

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
                  Актуальные сеансы с жанром и описанием — удобно при планировании поездки из Пушкинских Гор.
                </p>
              </div>
              <div className="afisha-cinema-grid">
                {cinemaPskov.map((event) => (
                  <EventCard key={event.id} event={event} variant="cinema" />
                ))}
              </div>
            </section>
          )}

          {pushkinEvents.length > 0 && (
            <section className="afisha-section" aria-labelledby="pg-heading">
              <div className="afisha-section-head">
                <h2 id="pg-heading">🏛 Пушкинские Горы</h2>
                <p className="afisha-section-lead">Музей-заповедник, экскурсии и праздники для туристов и жителей.</p>
              </div>
              <div className="afisha-grid">
                {pushkinEvents.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            </section>
          )}

          {pskovOther.length > 0 && (
            <section className="afisha-section" aria-labelledby="pskov-heading">
              <div className="afisha-section-head">
                <h2 id="pskov-heading">🏰 Псков</h2>
                <p className="afisha-section-lead">Концерты, выставки и городские мероприятия.</p>
              </div>
              <div className="afisha-grid">
                {pskovOther.map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            </section>
          )}
        </div>
      ) : (
        <div className="afisha-grid">
          {flatList.map((event) => (
            <EventCard
              key={event.id}
              event={event}
              variant={isCinemaEvent(event) ? "cinema" : "grid"}
            />
          ))}
        </div>
      )}
    </div>
  );
}

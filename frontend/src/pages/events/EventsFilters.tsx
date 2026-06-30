import { Link } from "react-router-dom";

import { Input } from "@/components/ui/input";
import { eventSourceLabel } from "@/lib/eventUtils";

import type { EventsPageState } from "./useEventsPage";

type EventsFiltersProps = Pick<
  EventsPageState,
  | "EVENT_REGION_FILTERS"
  | "categoryFilter"
  | "categoryFilters"
  | "eventsBase"
  | "garnectOnly"
  | "regionFilter"
  | "resetSearch"
  | "search"
  | "searchInput"
  | "setCategoryFilter"
  | "setRegionFilter"
  | "setSearchInput"
  | "sourceFilter"
>;

export function EventsFilters({
  EVENT_REGION_FILTERS,
  categoryFilter,
  categoryFilters,
  eventsBase,
  garnectOnly,
  regionFilter,
  resetSearch,
  search,
  searchInput,
  setCategoryFilter,
  setRegionFilter,
  setSearchInput,
  sourceFilter,
}: EventsFiltersProps) {
  const showRegionChips = !garnectOnly && !sourceFilter;

  return (
    <section className="page-panel page-panel--gold mb-6 events-filters-panel" aria-label="Поиск и фильтры афиши">
      <div className="flex flex-col sm:flex-row gap-2 mb-3">
        <Input
          placeholder="Поиск: концерт, кино, ярмарка…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="flex-1 pushkin-select"
        />
        {search && (
          <button type="button" className="literary-btn literary-btn--ghost shrink-0 text-sm" onClick={resetSearch}>
            Сбросить поиск
          </button>
        )}
      </div>

      {garnectOnly ? (
        <div className="literary-filter-bar">
          <Link to={eventsBase} className="filter-chip filter-chip-active no-underline">
            Бугровский гарнец ×
          </Link>
        </div>
      ) : showRegionChips ? (
        <div className="events-region-filters mb-0" role="group" aria-label="Регион">
          {EVENT_REGION_FILTERS.map((item) => (
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
      ) : null}

      {sourceFilter && (
        <div className="literary-filter-bar mt-3">
          <Link to={eventsBase} className="filter-chip filter-chip-active no-underline">
            {eventSourceLabel(sourceFilter)} ×
          </Link>
        </div>
      )}

      {!garnectOnly && !sourceFilter && categoryFilters.length > 1 && (
        <div className="literary-filter-bar mt-3">
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
    </section>
  );
}

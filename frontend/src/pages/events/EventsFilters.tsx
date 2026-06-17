import { Link } from "react-router-dom";

import { LiterarySectionHead } from "@/components/literary";
import { Input } from "@/components/ui/input";
import { eventSourceLabel } from "@/lib/eventUtils";

import type { EventsPageState } from "./useEventsPage";

type EventsFiltersProps = Pick<
  EventsPageState,
  | "EVENT_REGION_FILTERS"
  | "applySearch"
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
  applySearch,
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
  return (
    <section className="page-panel page-panel--gold mb-6">
      <LiterarySectionHead
        kicker="🔍 Поиск"
        title={garnectOnly ? "Найти в программе" : "Найти в афише"}
        compact
      />
      <div className="flex flex-col sm:flex-row gap-2 mb-4">
        <Input
          placeholder="Поиск: концерт, кино, ярмарка…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && applySearch()}
          className="flex-1 pushkin-select"
        />
        <button type="button" className="literary-btn literary-btn--primary shrink-0" onClick={applySearch}>
          Найти
        </button>
        {search && (
          <button type="button" className="literary-btn literary-btn--ghost shrink-0 text-sm" onClick={resetSearch}>
            Сбросить
          </button>
        )}
      </div>

      {garnectOnly ? (
        <div className="literary-filter-bar mt-4">
          <Link to={eventsBase} className="filter-chip filter-chip-active no-underline">
            Бугровский гарнец ×
          </Link>
        </div>
      ) : (
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
      )}

      {sourceFilter && (
        <div className="literary-filter-bar mt-4">
          <Link to={eventsBase} className="filter-chip filter-chip-active no-underline">
            {eventSourceLabel(sourceFilter)} ×
          </Link>
        </div>
      )}

      {!garnectOnly && !sourceFilter && categoryFilters.length > 1 && (
        <div className="literary-filter-bar mt-4">
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

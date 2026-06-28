import { PageHeader } from "@/components/PageHeader";

import { EventsDashboard } from "./events/EventsDashboard";
import { EventsFilters } from "./events/EventsFilters";
import { EventsGarnectAlerts } from "./events/EventsGarnectAlerts";
import { EventsStatsRibbon } from "./events/EventsStatsRibbon";
import { useEventsPage } from "./events/useEventsPage";

export function EventsPage() {
  const events = useEventsPage();

  return (
    <div className="literary-page page-section max-w-6xl events-page">
      <PageHeader icon={events.pageIcon} title={events.pageTitle} subtitle={events.pageSubtitle}>
        {events.garnectOnly && (
          <button type="button" className="literary-btn literary-btn--ghost text-sm" onClick={events.shareGarnect}>
            Поделиться
          </button>
        )}
      </PageHeader>

      {events.shareMsg && <p className="alert-success mb-4">{events.shareMsg}</p>}

      <EventsGarnectAlerts
        eventsBase={events.eventsBase}
        garnectOnly={events.garnectOnly}
        garnectProgram={events.garnectProgram}
      />

      {!events.garnectOnly && !events.sourceFilter && (
        <EventsStatsRibbon totalVisible={events.loading ? undefined : events.visibleEvents.length} />
      )}

      <EventsFilters
        EVENT_REGION_FILTERS={events.EVENT_REGION_FILTERS}
        applySearch={events.applySearch}
        categoryFilter={events.categoryFilter}
        categoryFilters={events.categoryFilters}
        eventsBase={events.eventsBase}
        garnectOnly={events.garnectOnly}
        regionFilter={events.regionFilter}
        resetSearch={events.resetSearch}
        search={events.search}
        searchInput={events.searchInput}
        setCategoryFilter={events.setCategoryFilter}
        setRegionFilter={events.setRegionFilter}
        setSearchInput={events.setSearchInput}
        sourceFilter={events.sourceFilter}
      />

      <EventsDashboard
        EVENTS_COPY={events.EVENTS_COPY}
        cinemaEvents={events.cinemaEvents}
        garnectEventsPath={events.garnectEventsPath}
        garnectOnly={events.garnectOnly}
        garnectProgram={events.garnectProgram}
        garnectShareUrl={events.garnectShareUrl}
        loadError={events.loadError}
        loading={events.loading}
        reload={events.reload}
        pskovEvents={events.pskovEvents}
        pushkinOtherEvents={events.pushkinOtherEvents}
        regionFilter={events.regionFilter}
        search={events.search}
        showCityRow={events.showCityRow}
        showGarnectOnlyBlock={events.showGarnectOnlyBlock}
        showPushkinBlock={events.showPushkinBlock}
        showPskovOnlyBlock={events.showPskovOnlyBlock}
        showSourceOnlyBlock={events.showSourceOnlyBlock}
        visibleEvents={events.visibleEvents}
      />
    </div>
  );
}

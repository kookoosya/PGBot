import { PageHeader } from "@/components/PageHeader";

import { EventsDashboard } from "./events/EventsDashboard";
import { EventsFilters } from "./events/EventsFilters";
import { EventsGarnectAlerts } from "./events/EventsGarnectAlerts";
import { EventsStatsRibbon } from "./events/EventsStatsRibbon";
import { useEventsPage } from "./events/useEventsPage";

const FLOW_STEPS = [
  { icon: "🔍", title: "Найдите", text: "Поиск, регион или категория — посёлок, Псков и кино." },
  { icon: "📅", title: "Откройте событие", text: "Дата, место, описание и ссылка на источник." },
  { icon: "🔗", title: "Поделитесь", text: "Отправьте ссылку друзьям или откройте во ВК-боте." },
];

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

      {!events.garnectOnly && !events.sourceFilter && (
        <section className="page-section pb-2" aria-label="Как пользоваться афишей">
          <div className="complaints-flow map-flow">
            {FLOW_STEPS.map((step) => (
              <div key={step.title} className="complaints-flow-step">
                <span className="complaints-flow-icon" aria-hidden>{step.icon}</span>
                <div>
                  <p className="complaints-flow-title m-0">{step.title}</p>
                  <p className="complaints-flow-text m-0">{step.text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {events.shareMsg && <p className="alert-success mb-4">{events.shareMsg}</p>}

      <EventsGarnectAlerts
        eventsBase={events.eventsBase}
        garnectOnly={events.garnectOnly}
        garnectProgram={events.garnectProgram}
      />

      {!events.garnectOnly && !events.sourceFilter && (
        <EventsStatsRibbon
          totalVisible={events.loading ? undefined : events.visibleEvents.length}
          regionFilter={events.regionFilter}
          onRegionClick={events.setRegionFilter}
        />
      )}

      <EventsFilters
        EVENT_REGION_FILTERS={events.EVENT_REGION_FILTERS}
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

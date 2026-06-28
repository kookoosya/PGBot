import { useState } from "react";

import { PAGE_SECTIONS } from "@/lib/literaryCopy";
import type { MapRoute, TaxiService } from "@/lib/api/types/places";

import { HotlinesPanel } from "./HotlinesPanel";
import { MapRoutesPanel } from "./MapRoutesPanel";
import { TaxiPanel } from "./TaxiPanel";

type ServiceTab = "routes" | "taxi" | "hotlines";

type MapServicesTabsProps = {
  routes: MapRoute[];
  activeRoute: MapRoute | null;
  onSelectRoute: (route: MapRoute) => void;
  onClearRoute: () => void;
  taxi: TaxiService[];
};

const TABS: { id: ServiceTab; label: string; icon: string }[] = [
  { id: "routes", label: "Маршруты", icon: "🧭" },
  { id: "taxi", label: "Такси", icon: "🚕" },
  { id: "hotlines", label: "Номера", icon: "📞" },
];

export function MapServicesTabs({
  routes,
  activeRoute,
  onSelectRoute,
  onClearRoute,
  taxi,
}: MapServicesTabsProps) {
  const [tab, setTab] = useState<ServiceTab>("routes");
  const [expanded, setExpanded] = useState(false);

  const summary = [
    routes.length ? `${routes.length} маршр.` : null,
    taxi.length ? `${taxi.length} такси` : null,
    "14 номеров",
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <section className="page-section map-services" aria-label="Справочник на карте">
      <button
        type="button"
        className="map-services-toggle lg:hidden"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <span>{expanded ? "▾" : "▸"} Справочник</span>
        <span className="map-services-toggle-hint">{summary}</span>
      </button>

      <div className={`map-services-inner${expanded ? " map-services-inner-open" : ""}`}>
        <div className="map-services-tabs" role="tablist">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              role="tab"
              aria-selected={tab === t.id}
              className={`map-services-tab${tab === t.id ? " map-services-tab-active" : ""}`}
              onClick={() => setTab(t.id)}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        <div className="map-services-panel" role="tabpanel">
          {tab === "routes" && (
            <MapRoutesPanel
              compact
              routes={routes}
              activeRoute={activeRoute}
              onSelectRoute={(r) => {
                onSelectRoute(r);
                setExpanded(true);
              }}
              onClearRoute={onClearRoute}
            />
          )}
          {tab === "taxi" && <TaxiPanel compact taxi={taxi} />}
          {tab === "hotlines" && <HotlinesPanel compact />}
        </div>
      </div>

      <p className="map-services-footnote m-0 text-xs text-muted-foreground hidden lg:block">
        {PAGE_SECTIONS.map.lead}
      </p>
    </section>
  );
}

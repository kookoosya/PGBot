import { geoNavigateUrl, yandexMapsPointUrl, yandexRouteUrl } from "@/lib/mapLinks";
import { LiterarySectionHead } from "@/components/literary";
import type { MapRoute } from "@/lib/api/types/places";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";

type MapRoutesPanelProps = {
  routes: MapRoute[];
  activeRoute: MapRoute | null;
  onSelectRoute: (route: MapRoute) => void;
  onClearRoute: () => void;
  compact?: boolean;
};

export function MapRoutesPanel({
  routes,
  activeRoute,
  onSelectRoute,
  onClearRoute,
  compact = false,
}: MapRoutesPanelProps) {
  if (routes.length === 0) return null;

  const copy = PAGE_SECTIONS.map.routes;

  return (
    <div className={compact ? "map-routes-compact" : "page-section pb-3"}>
      <div className={`page-panel page-panel--gold map-routes-panel${compact ? " map-routes-panel-compact" : ""}`}>
        {!compact && (
          <LiterarySectionHead kicker={copy.kicker} title={copy.title} lead={copy.lead} />
        )}
        <div className="map-routes-grid">
          {routes.map((route) => (
            <button
              key={route.id}
              type="button"
              className={`map-route-card${activeRoute?.id === route.id ? " map-route-card-active" : ""}`}
              onClick={() => onSelectRoute(route)}
            >
              <strong>{route.title}</strong>
              <span className="text-xs opacity-80">{route.duration}</span>
              <p className="text-xs m-0 mt-1">{route.description}</p>
            </button>
          ))}
        </div>
        {activeRoute && (
          <div className="map-route-detail">
            <div className="flex items-center justify-between gap-2 mt-3">
              <h4 className="m-0 text-sm font-bold">{activeRoute.title}</h4>
              <button type="button" className="text-xs opacity-70" onClick={onClearRoute}>
                Скрыть
              </button>
            </div>
            <p className="text-xs text-muted-foreground m-0 mt-1">
              {activeRoute.duration} · {activeRoute.description}
            </p>
            <p className="text-xs m-0 mt-1 opacity-75">Маршрут на карте — ориентировочная линия между точками</p>
            <ol className="map-route-stops">
              {activeRoute.stops.map((stop, i) => (
                <li key={`${stop.name}-${i}`} className="map-route-stop">
                  <span className="map-route-stop-num">{i + 1}</span>
                  <div>
                    <strong className="text-sm">{stop.name}</strong>
                    {stop.address && <p className="text-xs text-muted-foreground m-0">{stop.address}</p>}
                    <div className="map-route-stop-links">
                      <a href={yandexMapsPointUrl(stop.latitude, stop.longitude, stop.name)} target="_blank" rel="noopener noreferrer" className="text-xs">
                        Яндекс.Карты
                      </a>
                      <a href={yandexRouteUrl(stop.latitude, stop.longitude)} target="_blank" rel="noopener noreferrer" className="text-xs">
                        Маршрут
                      </a>
                      <a href={geoNavigateUrl(stop.latitude, stop.longitude)} className="text-xs">
                        GPS
                      </a>
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}

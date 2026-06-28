import { MapContainer, Polyline, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.markercluster/dist/MarkerCluster.css";
import "leaflet.markercluster/dist/MarkerCluster.Default.css";
import "leaflet.markercluster";

import { PageHeader } from "@/components/PageHeader";
import { MAP_TILE_OSM, MAP_TILE_SAT } from "@/lib/mapTiles";
import { PAGE_SECTIONS } from "@/lib/literaryCopy";

import { MAP_CENTER } from "./map/constants";
import { ClusterLayer, FlyToPlace, MapEvents, RouteStopsLayer } from "./map/MapLayers";
import { MapRoutesPanel } from "./map/MapRoutesPanel";
import { PlaceDetailPanel } from "./map/PlaceDetailPanel";
import { PlacesList } from "./map/PlacesList";
import { TaxiPanel } from "./map/TaxiPanel";
import { HotlinesPanel } from "./map/HotlinesPanel";
import { useMapPage } from "./map/useMapPage";
import { formatSyncAge } from "@/lib/formatSyncAge";

export function MapPage() {
  const map = useMapPage();

  const handleOpenPlace = (id: number) => {
    map.openPlace(id);
    map.setMobileTab("map");
  };

  return (
    <div className="literary-page">
      <div className="page-section pb-2">
        <PageHeader
          icon="🗺"
          title={PAGE_SECTIONS.map.title}
          subtitle={PAGE_SECTIONS.map.lead}
        />
      </div>

      <MapRoutesPanel
        routes={map.routes}
        activeRoute={map.activeRoute}
        onSelectRoute={map.showRoute}
        onClearRoute={() => map.setActiveRoute(null)}
      />

      <TaxiPanel taxi={map.taxi} taxiMode={map.taxiMode} />

      <HotlinesPanel />

      <div className="map-mobile-tabs lg:hidden page-section pb-2">
        <button
          type="button"
          className={`map-mobile-tab ${map.mobileTab === "map" ? "map-mobile-tab-active" : ""}`}
          onClick={() => map.setMobileTab("map")}
        >
          🗺 Карта
        </button>
        <button
          type="button"
          className={`map-mobile-tab ${map.mobileTab === "list" ? "map-mobile-tab-active" : ""}`}
          onClick={() => map.setMobileTab("list")}
        >
          📋 Список ({map.places.length})
        </button>
      </div>

      <div className="flex flex-col lg:flex-row map-layout">
        <div className={`map-pane flex-1 relative ${map.mobileTab === "list" ? "map-pane-hidden-mobile" : ""}`}>
          <MapContainer center={MAP_CENTER} zoom={14} className="map-canvas z-0" scrollWheelZoom>
            <TileLayer
              attribution={map.mapStyle === "scheme"
                ? "© OpenStreetMap · справочник посёлка"
                : "© Esri"}
              url={map.mapStyle === "scheme" ? MAP_TILE_OSM : MAP_TILE_SAT}
            />
            <MapEvents onBounds={map.loadPlaces} pausedRef={map.boundsPausedRef} />
            <ClusterLayer places={map.places} onSelect={map.openPlace} />
            {map.activeRoute && map.activeRoute.stops.length > 1 && (
              <>
                <Polyline
                  positions={map.activeRoute.stops.map((s) => [s.latitude, s.longitude] as [number, number])}
                  pathOptions={{ color: "#c9a227", weight: 4, opacity: 0.85, dashArray: "10 8" }}
                />
                <RouteStopsLayer route={map.activeRoute} />
              </>
            )}
            <FlyToPlace place={map.highlight} pausedRef={map.boundsPausedRef} />
          </MapContainer>

          {map.taxiMode && (
            <div className="map-taxi-overlay" aria-hidden>
              <p>🚕 Режим такси — выберите службу выше</p>
            </div>
          )}

          <div className="map-overlay-controls">
            <button type="button" className={`map-layer-btn ${map.mapStyle === "scheme" ? "active" : ""}`} onClick={() => map.setMapStyle("scheme")}>
              Схема
            </button>
            <button type="button" className={`map-layer-btn ${map.mapStyle === "satellite" ? "active" : ""}`} onClick={() => map.setMapStyle("satellite")}>
              Спутник
            </button>
          </div>

          {map.mapStats && (
            <div className="map-stats-overlay">
              <p className="font-bold m-0 text-sm">📍 {map.mapStats.total_places} мест</p>
              <p className="text-xs text-muted-foreground m-0 mt-1">
                {formatSyncAge(map.mapStats.last_sync)}
              </p>
            </div>
          )}
        </div>

        <div className={`w-full lg:w-[420px] border-l map-sidebar map-sidebar-glass overflow-y-auto ${map.mobileTab === "map" ? "map-sidebar-hidden-mobile" : ""}`}>
          <div className="p-4 space-y-3 border-b sticky top-0 map-sidebar-head z-10">
            <input
              className="pushkin-select w-full"
              placeholder="Поиск организации..."
              value={map.search}
              onChange={(e) => map.setSearch(e.target.value)}
            />
            <div className="map-filter-scroll">
              {map.mapModes.map((f) => (
                <button
                  key={f.id}
                  type="button"
                  className={`map-filter-chip${map.activeFilterId === f.id ? " map-filter-chip-active" : ""}`}
                  onClick={() => map.applyQuickFilter(f)}
                >
                  {f.label}
                </button>
              ))}
            </div>
            <div className="map-filter-row">
              <select
                className="pushkin-select text-sm flex-1"
                value={map.shopsOnly ? "" : map.category}
                onChange={(e) => {
                  map.setShopsOnly(false);
                  map.setUsefulOnly(false);
                  map.setCategory(e.target.value);
                }}
              >
                <option value="">Все категории</option>
                {map.categories.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
              <button
                type="button"
                className="map-offline-btn"
                onClick={map.handleOfflineDownload}
                disabled={map.offlineBusy}
                title={map.offlineReady ? "Офлайн-карта сохранена — обновить" : "Скачать карту и точки для офлайн"}
                aria-label={map.offlineReady ? "Обновить офлайн-карту" : "Скачать офлайн-карту"}
              >
                {map.offlineBusy ? "…" : map.offlineReady ? "📥 Обновить" : "📥 Офлайн"}
              </button>
            </div>
            {map.offlineMsg ? <p className="text-xs text-muted-foreground">{map.offlineMsg}</p> : null}
          </div>

          {map.selected ? (
            <PlaceDetailPanel
              selected={map.selected}
              tab={map.tab}
              setTab={map.setTab}
              msg={map.msg}
              msgType={map.msgType}
              reviewForm={map.reviewForm}
              setReviewForm={map.setReviewForm}
              complaintForm={map.complaintForm}
              setComplaintForm={map.setComplaintForm}
              reportForm={map.reportForm}
              setReportForm={map.setReportForm}
              complaintTypes={map.complaintTypes}
              mapReportTypes={map.mapReportTypes}
              submitReview={map.submitReview}
              submitComplaint={map.submitComplaint}
              submitReport={map.submitReport}
              clearSelection={map.clearSelection}
            />
          ) : (
            <PlacesList
              places={map.places}
              placesLoading={map.placesLoading}
              placesError={map.placesError}
              onOpenPlace={handleOpenPlace}
              onRetry={() => map.loadPlaces(map.boundsRef.current ?? undefined)}
            />
          )}
        </div>
      </div>

    </div>
  );
}

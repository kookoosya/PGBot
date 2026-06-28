import { useEffect, useState } from "react";

import { api } from "@/lib/api/index";
import type { PublicEventsStats } from "@/lib/api/types/events";
import { formatSyncAge } from "@/lib/formatSyncAge";

type EventsStatsRibbonProps = {
  totalVisible?: number;
};

export function EventsStatsRibbon({ totalVisible }: EventsStatsRibbonProps) {
  const [stats, setStats] = useState<PublicEventsStats | null>(null);

  const refresh = () => {
    api.getPublicEventsStats().then(setStats).catch(() => setStats(null));
  };

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 5 * 60_000);
    const onVisible = () => {
      if (document.visibilityState === "visible") refresh();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(interval);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  if (!stats) return null;

  const syncHint = stats.last_sync
    ? `Обновлено ${formatSyncAge(stats.last_sync)} · кино каждые ${stats.cinema_sync_hours} ч · полная ${stats.full_sync_hours} ч`
    : `Афиша обновляется автоматически · кино ${stats.cinema_sync_hours} ч · полная ${stats.full_sync_hours} ч`;

  const regionEntries = Object.entries(stats.by_region).sort((a, b) => b[1] - a[1]);

  return (
    <div className="page-section pb-2">
      <div className="map-stats-ribbon" aria-label="Статистика афиши">
        <div className="map-stats-ribbon-head">
          <p className="map-stats-ribbon-total m-0">
            <strong>{totalVisible ?? stats.total_events}</strong>{" "}
            {totalVisible != null && totalVisible !== stats.total_events
              ? "событий в выборке"
              : "событий в афише"}
          </p>
          <p className="map-stats-ribbon-sync m-0" title={syncHint}>
            {syncHint}
          </p>
        </div>
        {regionEntries.length > 0 && (
          <div className="map-stats-ribbon-bars">
            {regionEntries.map(([region, count]) => (
              <div key={region} className="map-cat-bar map-cat-bar-static" title={`${region}: ${count}`}>
                <span className="map-cat-bar-label">
                  {region === "Пушкинские Горы" ? "🏔" : region === "Псков" ? "🏙" : "📍"} {region}
                </span>
                <span className="map-cat-bar-track" aria-hidden>
                  <span
                    className="map-cat-bar-fill"
                    style={{
                      width: `${Math.max(12, (count / (regionEntries[0]?.[1] ?? 1)) * 100)}%`,
                    }}
                  />
                </span>
                <span className="map-cat-bar-count">{count}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

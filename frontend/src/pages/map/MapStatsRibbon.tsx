import type { MapStats } from "@/lib/api/types/places";
import { formatSyncAge } from "@/lib/formatSyncAge";

import { CATEGORY_ICONS } from "./constants";

type MapStatsRibbonProps = {
  stats: MapStats | null;
  activeCategory: string;
  onCategoryClick: (category: string) => void;
};

const CATEGORY_LABELS: Record<string, string> = {
  supermarket: "Магазины",
  pharmacy: "Аптеки",
  culture: "Культура",
  hospital: "Медицина",
  cafe: "Кафе",
  government: "Службы",
  transport: "Транспорт",
  hotel: "Жильё",
  gas: "АЗС",
  post: "Почта",
  bank: "Банки",
  parking: "Парковки",
};

export function MapStatsRibbon({ stats, activeCategory, onCategoryClick }: MapStatsRibbonProps) {
  if (!stats) return null;

  const entries = Object.entries(stats.by_category)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);
  const maxCount = entries[0]?.[1] ?? 1;

  return (
    <div className="page-section pb-2">
      <div className="map-stats-ribbon" aria-label="Статистика карты">
        <div className="map-stats-ribbon-head">
          <p className="map-stats-ribbon-total m-0">
            <strong>{stats.total_places}</strong> мест на карте
          </p>
          <p className="map-stats-ribbon-sync m-0">{formatSyncAge(stats.last_sync)}</p>
        </div>
        <div className="map-stats-ribbon-bars">
          {entries.map(([cat, count]) => {
            const label = CATEGORY_LABELS[cat] ?? cat;
            const icon = CATEGORY_ICONS[cat] ?? "📍";
            const active = activeCategory === cat;
            return (
              <button
                key={cat}
                type="button"
                className={`map-cat-bar${active ? " map-cat-bar-active" : ""}`}
                onClick={() => onCategoryClick(active ? "" : cat)}
                title={`${label}: ${count}`}
              >
                <span className="map-cat-bar-label">
                  {icon} {label}
                </span>
                <span className="map-cat-bar-track" aria-hidden>
                  <span
                    className="map-cat-bar-fill"
                    style={{ width: `${Math.max(12, (count / maxCount) * 100)}%` }}
                  />
                </span>
                <span className="map-cat-bar-count">{count}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

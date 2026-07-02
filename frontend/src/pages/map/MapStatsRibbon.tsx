import type { MapStats } from "@/lib/api/types/places";
import { formatSyncAge } from "@/lib/formatSyncAge";

import { CategoryIcon } from "./categoryIcons";
import { CATEGORY_COLORS } from "./constants";

type MapStatsRibbonProps = {
  stats: MapStats | null;
  categories: { value: string; label: string }[];
  activeCategory: string;
  onCategoryClick: (category: string) => void;
};

const FALLBACK_LABELS: Record<string, string> = {
  supermarket: "Магазины",
  shop: "Магазины",
  pharmacy: "Аптеки",
  culture: "Культура",
  hospital: "Медицина",
  vet: "Ветеринария",
  cafe: "Кафе",
  restaurant: "Еда",
  government: "Службы",
  transport: "Транспорт",
  hotel: "Жильё",
  gas: "АЗС",
  post: "Почта",
  bank: "Банк",
  parking: "Парковки",
  beauty: "Красота",
  school: "Школа",
  tyre: "Шины",
  auto: "Авто",
};

export function MapStatsRibbon({
  stats,
  categories,
  activeCategory,
  onCategoryClick,
}: MapStatsRibbonProps) {
  if (!stats) return null;

  const labelFor = (cat: string) =>
    categories.find((c) => c.value === cat)?.label ?? FALLBACK_LABELS[cat] ?? cat;

  const entries = Object.entries(stats.by_category)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8);
  const maxCount = entries[0]?.[1] ?? 1;
  const syncHours = stats.auto_sync_hours ?? 6;
  const syncHint = stats.last_sync
    ? `Обновлено ${formatSyncAge(stats.last_sync)} · авто каждые ${syncHours} ч`
    : `Справочник обновляется автоматически каждые ${syncHours} ч`;
  const refCount = stats.reference_places ?? 0;
  const accuracyHint = refCount > 0
    ? `${refCount} записей справочника портала · остальное — открытые карты${stats.yandex_live ? " и Яндекс" : " (OSM)"}`
    : "Точки из открытых карт — уточняйте адрес и часы перед визитом";

  return (
    <div className="page-section pb-2">
      <div className="map-stats-ribbon" aria-label="Статистика карты">
        <div className="map-stats-ribbon-head">
          <p className="map-stats-ribbon-total m-0">
            <strong>{stats.total_places}</strong> мест на карте
            {refCount > 0 ? ` · ${refCount} справочник портала` : ""}
            {stats.yandex_live ? " · живые данные Яндекс" : ""}
          </p>
          <p className="map-stats-ribbon-sync m-0" title={syncHint}>
            {syncHint}
          </p>
          <p className="map-stats-ribbon-accuracy m-0" title={accuracyHint}>
            {accuracyHint}
          </p>
        </div>
        <div className="map-stats-ribbon-bars">
          {entries.map(([cat, count]) => {
            const label = labelFor(cat);
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
                  <CategoryIcon
                    category={cat}
                    className="map-category-icon"
                    size={15}
                    color={CATEGORY_COLORS[cat] ?? CATEGORY_COLORS.other}
                  />
                  {label}
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

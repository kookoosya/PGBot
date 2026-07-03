import type { MapStats } from "@/lib/api/types/places";
import { formatSyncAge } from "@/lib/formatSyncAge";

import { CATEGORY_ICONS } from "./constants";

type MapStatsRibbonProps = {
  stats: MapStats | null;
  categories: { value: string; label: string }[];
  activeCategory: string;
  onCategoryClick: (category: string) => void;
  currentAreaCount: number | null;
  hasActiveFilter?: boolean;
  incompatibleFilterLoading?: boolean;
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
  car_wash: "Мойка",
  auto_parts: "Запчасти",
  towing: "Эвакуатор",
};

const TOP_CATEGORY_LIMIT = 8;

export function sumCategoryCounts(byCategory: Record<string, number>): number {
  return Object.values(byCategory).reduce((sum, n) => sum + n, 0);
}

export function topCategoryEntries(byCategory: Record<string, number>, limit = TOP_CATEGORY_LIMIT) {
  return Object.entries(byCategory)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit);
}

export function hiddenCategoryTotal(byCategory: Record<string, number>, limit = TOP_CATEGORY_LIMIT): number {
  const total = sumCategoryCounts(byCategory);
  const visible = topCategoryEntries(byCategory, limit).reduce((sum, [, n]) => sum + n, 0);
  return Math.max(0, total - visible);
}

export function MapStatsRibbon({
  stats,
  categories,
  activeCategory,
  onCategoryClick,
  currentAreaCount,
  hasActiveFilter = false,
  incompatibleFilterLoading = false,
}: MapStatsRibbonProps) {
  if (!stats) return null;

  const labelFor = (cat: string) =>
    categories.find((c) => c.value === cat)?.label ?? FALLBACK_LABELS[cat] ?? cat;

  const entries = topCategoryEntries(stats.by_category);
  const maxCount = entries[0]?.[1] ?? 1;
  const catalogTotal = stats.catalog_places ?? stats.total_places;
  const mappableTotal = stats.mappable_places ?? catalogTotal;
  const hiddenTotal = hiddenCategoryTotal(stats.by_category);
  const syncHours = stats.auto_sync_hours ?? 6;
  const syncHint = stats.last_sync
    ? `Обновлено ${formatSyncAge(stats.last_sync)} · авто каждые ${syncHours} ч`
    : `Справочник обновляется автоматически каждые ${syncHours} ч`;
  const refCount = stats.reference_places ?? 0;
  const accuracyHint = refCount > 0
    ? `${refCount} записей справочника портала · остальное — открытые карты${stats.yandex_live ? " и Яндекс" : " (OSM)"}`
    : "Точки из открытых карт — уточняйте адрес и часы перед визитом";

  const areaLabel = hasActiveFilter
    ? "По фильтру в видимой области"
    : "В видимой области";

  return (
    <div className="page-section pb-2">
      <div className="map-stats-ribbon" aria-label="Статистика карты">
        <div className="map-stats-ribbon-head">
          <p className="map-stats-ribbon-total m-0">
            Всего в справочнике: <strong>{catalogTotal}</strong>
          </p>
          {mappableTotal !== catalogTotal ? (
            <p className="map-stats-ribbon-total m-0">
              С координатами на карте: <strong>{mappableTotal}</strong>
            </p>
          ) : null}
          {incompatibleFilterLoading ? (
            <p className="map-stats-ribbon-total m-0">Обновляем список…</p>
          ) : currentAreaCount != null ? (
            <p className="map-stats-ribbon-total m-0">
              {areaLabel}: <strong>{currentAreaCount}</strong>
            </p>
          ) : null}
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
        {hiddenTotal > 0 ? (
          <p className="map-stats-ribbon-hidden m-0 text-sm text-muted-foreground">
            Остальные категории: <strong>{hiddenTotal}</strong> организаций · раскройте «Ещё категории» ниже
          </p>
        ) : null}
      </div>
    </div>
  );
}

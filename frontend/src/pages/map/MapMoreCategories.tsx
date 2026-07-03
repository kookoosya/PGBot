import { CATEGORY_ICONS } from "./constants";

type MapMoreCategoriesProps = {
  topCategories: string[];
  categories: { value: string; label: string }[];
  activeCategory: string;
  onSelect: (category: string) => void;
  categoryCounts?: Record<string, number>;
};

export function MapMoreCategories({
  topCategories,
  categories,
  activeCategory,
  onSelect,
  categoryCounts = {},
}: MapMoreCategoriesProps) {
  const more = categories.filter((c) => !topCategories.includes(c.value));
  if (!more.length) return null;

  const activeInMore = more.some((c) => c.value === activeCategory);
  const moreTotal = more.reduce((sum, c) => sum + (categoryCounts[c.value] ?? 0), 0);

  return (
    <details className="map-more-categories" open={activeInMore}>
      <summary className="map-more-categories-summary">
        Ещё категории ({more.length}{moreTotal > 0 ? ` · ${moreTotal} организаций` : ""})
      </summary>
      <div className="map-filter-scroll mt-2">
        {more.map((c) => {
          const count = categoryCounts[c.value];
          return (
            <button
              key={c.value}
              type="button"
              className={`map-filter-chip${activeCategory === c.value ? " map-filter-chip-active" : ""}`}
              onClick={() => onSelect(activeCategory === c.value ? "" : c.value)}
            >
              {CATEGORY_ICONS[c.value] ?? "📍"} {c.label}
              {count != null ? ` (${count})` : ""}
            </button>
          );
        })}
      </div>
    </details>
  );
}

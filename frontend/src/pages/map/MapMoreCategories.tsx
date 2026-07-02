import { CategoryIcon } from "./categoryIcons";
import { CATEGORY_COLORS } from "./constants";

type MapMoreCategoriesProps = {
  topCategories: string[];
  categories: { value: string; label: string }[];
  activeCategory: string;
  onSelect: (category: string) => void;
};

export function MapMoreCategories({
  topCategories,
  categories,
  activeCategory,
  onSelect,
}: MapMoreCategoriesProps) {
  const more = categories.filter((c) => !topCategories.includes(c.value));
  if (!more.length) return null;

  const activeInMore = more.some((c) => c.value === activeCategory);

  return (
    <details className="map-more-categories" open={activeInMore}>
      <summary className="map-more-categories-summary">
        Ещё категории ({more.length})
      </summary>
      <div className="map-filter-scroll mt-2">
        {more.map((c) => (
          <button
            key={c.value}
            type="button"
            className={`map-filter-chip${activeCategory === c.value ? " map-filter-chip-active" : ""}`}
            onClick={() => onSelect(activeCategory === c.value ? "" : c.value)}
          >
            <CategoryIcon
              category={c.value}
              className="map-category-icon"
              size={14}
              color={CATEGORY_COLORS[c.value] ?? CATEGORY_COLORS.other}
            />{" "}
            {c.label}
          </button>
        ))}
      </div>
    </details>
  );
}

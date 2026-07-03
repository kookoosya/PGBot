import { LiteraryEmptyState, LiteraryInlineLoader } from "@/components/literary";
import type { Place } from "@/lib/api/types/places";
import { EMPTY_STATES } from "@/lib/literaryCopy";
import { CATEGORY_ICONS } from "./constants";

type PlacesListProps = {
  places: Place[];
  placesLoading: boolean;
  placesError: boolean;
  count: number | null;
  hasActiveFilter?: boolean;
  incompatibleFilterLoading?: boolean;
  onOpenPlace: (id: number) => void;
  onRetry: () => void;
};

const emptyCopy = EMPTY_STATES.mapPlaces;
const errorCopy = EMPTY_STATES.mapPlacesError;

export function PlacesList({
  places,
  placesLoading,
  placesError,
  count,
  hasActiveFilter = false,
  incompatibleFilterLoading = false,
  onOpenPlace,
  onRetry,
}: PlacesListProps) {
  const countLabel = hasActiveFilter
    ? `По фильтру в видимой области: ${count ?? "…"}`
    : `В видимой области: ${count ?? "…"}`;

  if (placesError) {
    return (
      <div className="p-3">
        <LiteraryEmptyState
          icon={errorCopy.icon}
          title={errorCopy.title}
          text={errorCopy.text}
          compact
        >
          <button type="button" className="literary-btn literary-btn--outline mt-3" onClick={onRetry}>
            Повторить
          </button>
        </LiteraryEmptyState>
      </div>
    );
  }

  if (incompatibleFilterLoading) {
    return (
      <div className="p-4">
        <LiteraryInlineLoader label="Обновляем список…" />
      </div>
    );
  }

  if (placesLoading && places.length === 0) {
    return (
      <div className="p-4">
        <LiteraryInlineLoader label="Загружаем точки на карте…" />
      </div>
    );
  }

  if (!placesLoading && places.length === 0) {
    return (
      <div className="p-3">
        <p className="text-xs text-muted-foreground px-1 mb-2">{countLabel}</p>
        <LiteraryEmptyState
          icon={emptyCopy.icon}
          title={emptyCopy.title}
          text={emptyCopy.text}
          compact
        />
      </div>
    );
  }

  return (
    <div className="p-3 space-y-2">
      <p className="text-xs text-muted-foreground px-1">
        {countLabel}
        {placesLoading ? " · обновляем…" : ""}
      </p>
      {places.map((p) => (
        <button
          key={p.id}
          type="button"
          className="org-list-card"
          data-place-id={p.id}
          onClick={() => onOpenPlace(p.id)}
        >
          <span className="org-list-icon">{CATEGORY_ICONS[p.category] || "📍"}</span>
          <div className="org-list-body">
            <div className="flex justify-between gap-2 items-start">
              <strong className="text-sm text-left">{p.name}</strong>
              <div className="flex items-center gap-1 shrink-0">
                {p.display_rating > 0 && (
                  <span className="org-list-rating">★ {p.display_rating.toFixed(1)}</span>
                )}
              </div>
            </div>
            <p className="text-xs text-muted-foreground text-left">{p.category_label} · {p.address || "Пушкинские Горы"}</p>
            {p.phone && <p className="text-xs mt-1 text-left">📞 {p.phone}</p>}
          </div>
        </button>
      ))}
    </div>
  );
}

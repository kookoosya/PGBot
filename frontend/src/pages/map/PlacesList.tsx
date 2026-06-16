import { Button } from "@/components/ui/button";
import type { Place } from "@/lib/api";

import { CATEGORY_ICONS } from "./constants";

type PlacesListProps = {
  places: Place[];
  placesLoading: boolean;
  placesError: boolean;
  onOpenPlace: (id: number) => void;
  onRetry: () => void;
};

export function PlacesList({ places, placesLoading, placesError, onOpenPlace, onRetry }: PlacesListProps) {
  return (
    <div className="p-3 space-y-2">
      <p className="text-xs text-muted-foreground px-1">
        {placesLoading
          ? "Загрузка…"
          : placesError
            ? "Ошибка загрузки"
            : `${places.length} на карте`}
      </p>
      {places.map((p) => (
        <button key={p.id} className="org-list-card" onClick={() => onOpenPlace(p.id)}>
          <span className="org-list-icon">{CATEGORY_ICONS[p.category] || "📍"}</span>
          <div className="org-list-body">
            <div className="flex justify-between gap-2 items-start">
              <strong className="text-sm text-left">{p.name}</strong>
              <div className="flex items-center gap-1 shrink-0">
                {p.rating_source === "reference" && (
                  <span className="org-list-ref" title="Проверенный справочник">✓</span>
                )}
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
      {!placesLoading && placesError && (
        <div className="text-center py-8 px-3">
          <p className="text-muted-foreground mb-3">Не удалось загрузить справочник</p>
          <Button size="sm" variant="outline" onClick={onRetry}>
            Повторить
          </Button>
        </div>
      )}
      {!placesLoading && !placesError && places.length === 0 && (
        <p className="text-center text-muted-foreground py-8">Ничего не найдено. Смените фильтр или поиск.</p>
      )}
    </div>
  );
}

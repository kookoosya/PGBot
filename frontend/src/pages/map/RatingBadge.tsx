import type { Place, PlaceDetail } from "@/lib/api/types/places";
export function RatingBadge({ place }: { place: Place | PlaceDetail }) {
  if (place.display_rating <= 0) return <span className="org-rating-none">Нет оценок</span>;
  return (
    <div className="org-rating-badge">
      <span className="org-rating-score">★ {place.display_rating.toFixed(1)}</span>
      <span className="org-rating-meta">
        {place.display_review_count} отзывов
        {place.rating_source === "yandex" && " · Яндекс"}
        {place.rating_source === "users" && " · жители"}
      </span>
    </div>
  );
}

interface CabinetSectionSkeletonProps {
  title?: string;
  lines?: number;
  className?: string;
}

/** Лёгкий скелетон секции кабинета пока грузятся обращения или объявления */
export function CabinetSectionSkeleton({
  title,
  lines = 3,
  className = "",
}: CabinetSectionSkeletonProps) {
  return (
    <div
      className={`literary-card literary-card--gold p-6 mb-6 cabinet-section-skeleton ${className}`.trim()}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={title ? `Загрузка: ${title}` : "Загрузка раздела"}
    >
      {title && <p className="literary-title text-lg m-0 mb-4">{title}</p>}
      <div className="space-y-3">
        {Array.from({ length: lines }, (_, i) => (
          <div
            key={i}
            className="cabinet-section-skeleton-line"
            style={{ width: i === lines - 1 ? "55%" : "100%" }}
          />
        ))}
      </div>
    </div>
  );
}

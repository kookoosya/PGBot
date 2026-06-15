interface LiteraryInlineLoaderProps {
  label?: string;
  className?: string;
  /** Компактный вид для блоков на главной */
  compact?: boolean;
}

/** Компактный литературный индикатор загрузки внутри страницы */
export function LiteraryInlineLoader({
  label = "Листаем альбом…",
  className = "",
  compact = false,
}: LiteraryInlineLoaderProps) {
  return (
    <div
      className={[
        "literary-page-loader",
        "literary-page-loader--inline",
        compact ? "literary-page-loader--compact" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <span className="literary-page-loader-icon" aria-hidden>🪶</span>
      <span>{label}</span>
    </div>
  );
}

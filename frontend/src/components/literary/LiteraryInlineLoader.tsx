interface LiteraryInlineLoaderProps {
  label?: string;
  className?: string;
}

/** Компактный литературный индикатор загрузки внутри страницы */
export function LiteraryInlineLoader({
  label = "Листаем альбом…",
  className = "",
}: LiteraryInlineLoaderProps) {
  return (
    <div className={`literary-page-loader literary-page-loader--inline ${className}`.trim()} role="status" aria-live="polite">
      <span className="literary-page-loader-icon" aria-hidden>🪶</span>
      <span>{label}</span>
    </div>
  );
}

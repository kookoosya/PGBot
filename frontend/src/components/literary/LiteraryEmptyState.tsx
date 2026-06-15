import type { ReactNode } from "react";

interface LiteraryEmptyStateProps {
  icon?: string;
  title: string;
  text: string;
  verse?: string;
  children?: ReactNode;
  /** Компактный вид для превью-блоков на главной */
  compact?: boolean;
}

export function LiteraryEmptyState({
  icon = "🪶",
  title,
  text,
  verse,
  children,
  compact = false,
}: LiteraryEmptyStateProps) {
  return (
    <div className={`literary-empty${compact ? " literary-empty--compact" : ""}`}>
      <div className="literary-empty-icon" aria-hidden>{icon}</div>
      <h3 className="literary-empty-title">{title}</h3>
      <p className="literary-empty-text">{text}</p>
      {children}
      {verse && <p className="literary-empty-verse">{verse}</p>}
    </div>
  );
}

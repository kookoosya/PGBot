import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface LiterarySectionHeadProps {
  kicker?: string;
  title: string;
  lead?: string;
  linkTo?: string;
  linkLabel?: string;
  /** Мета справа — дата обновления, счётчик и т.п. */
  meta?: ReactNode;
  children?: ReactNode;
  /** Светлые заголовки на тёмном фоне (кино-блок) */
  light?: boolean;
  className?: string;
}

export function LiterarySectionHead({
  kicker,
  title,
  lead,
  linkTo,
  linkLabel,
  meta,
  children,
  light = false,
  className = "",
}: LiterarySectionHeadProps) {
  return (
    <div className={`literary-section-head${light ? " literary-section-head--light" : ""} ${className}`.trim()}>
      <div>
        {kicker && <p className="literary-kicker">{kicker}</p>}
        <h2 className="literary-title">{title}</h2>
        {lead && <p className="literary-lead">{lead}</p>}
      </div>
      {(meta || (linkTo && linkLabel)) && (
        <div className="literary-section-head-aside">
          {meta && <div className="literary-section-meta">{meta}</div>}
          {linkTo && linkLabel && (
            <Link to={linkTo} className="literary-section-link">
              {linkLabel}
            </Link>
          )}
        </div>
      )}
      {children}
    </div>
  );
}

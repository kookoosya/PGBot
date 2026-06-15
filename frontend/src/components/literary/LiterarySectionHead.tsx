import type { ReactNode } from "react";
import { Link } from "react-router-dom";

interface LiterarySectionHeadProps {
  kicker?: string;
  title: string;
  lead?: string;
  linkTo?: string;
  linkLabel?: string;
  children?: ReactNode;
}

export function LiterarySectionHead({
  kicker,
  title,
  lead,
  linkTo,
  linkLabel,
  children,
}: LiterarySectionHeadProps) {
  return (
    <div className="literary-section-head">
      <div>
        {kicker && <p className="literary-kicker">{kicker}</p>}
        <h2 className="literary-title">{title}</h2>
        {lead && <p className="literary-lead">{lead}</p>}
      </div>
      {linkTo && linkLabel && (
        <Link to={linkTo} className="literary-section-link">
          {linkLabel}
        </Link>
      )}
      {children}
    </div>
  );
}

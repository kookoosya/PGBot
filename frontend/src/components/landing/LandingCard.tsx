import { Link } from "react-router-dom";
import type { ReactNode } from "react";

interface LandingCardProps {
  title: string;
  children: ReactNode;
  action?: { label: string; to: string };
  className?: string;
}

/** Единая карточка для блоков главной — одинаковые отступы и типографика. */
export function LandingCard({ title, children, action, className = "" }: LandingCardProps) {
  return (
    <article className={`landing-card ${className}`.trim()}>
      <h3 className="landing-card-title">{title}</h3>
      <div className="landing-card-body">{children}</div>
      {action && (
        <Link to={action.to} className="landing-card-action">
          {action.label}
        </Link>
      )}
    </article>
  );
}

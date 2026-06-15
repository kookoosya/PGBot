import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { LiterarySectionHead } from "./LiterarySectionHead";

interface CinemaSpotlightProps {
  children: ReactNode;
  linkTo?: string;
  linkLabel?: string;
}

export function CinemaSpotlight({ children, linkTo = "/events", linkLabel = "Все сеансы →" }: CinemaSpotlightProps) {
  return (
    <section className="cinema-spotlight" aria-label="Кино в Пскове">
      <div className="cinema-spotlight-grain" aria-hidden />
      <div className="cinema-spotlight-curtains" aria-hidden />
      <div className="cinema-spotlight-inner">
        <LiterarySectionHead
          kicker="🎬 Кинотеатры Пскова"
          title="Кино в Пскове"
          lead="Сеансы в областном центре — час дороги от Пушкинских Гор, целый вечер впечатлений."
          linkTo={linkTo}
          linkLabel={linkLabel}
        />
        {children}
      </div>
    </section>
  );
}

/** Светлая ссылка для тёмного фона кино-блока */
export function CinemaSpotlightLink({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link to={to} className="cinema-spotlight-link">
      {children}
    </Link>
  );
}

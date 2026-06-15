import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";
import { LiterarySectionHead } from "./LiterarySectionHead";

interface CinemaSpotlightProps {
  children: ReactNode;
  linkTo?: string;
  linkLabel?: string;
  /** Усиленный вид на главной */
  featured?: boolean;
  /** Пустое состояние — мягче свечение */
  empty?: boolean;
  kicker?: string;
  title?: string;
  lead?: string;
}

export function CinemaSpotlight({
  children,
  linkTo = "/events",
  linkLabel = "Все сеансы →",
  featured = false,
  empty = false,
  kicker = LANDING_SECTIONS.cinema.kicker,
  title = LANDING_SECTIONS.cinema.title,
  lead = LANDING_SECTIONS.cinema.lead,
}: CinemaSpotlightProps) {
  return (
    <section
      className={[
        "cinema-spotlight",
        featured ? "cinema-spotlight--featured" : "",
        empty ? "cinema-spotlight--empty" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      aria-label="Кино в Пскове"
    >
      <div className="cinema-spotlight-grain" aria-hidden />
      <div className="cinema-spotlight-curtains" aria-hidden />
      {featured && !empty && <div className="cinema-spotlight-glow" aria-hidden />}
      {featured && empty && <div className="cinema-spotlight-glow cinema-spotlight-glow--soft" aria-hidden />}
      <div className="cinema-spotlight-inner">
        <LiterarySectionHead
          kicker={kicker}
          title={title}
          lead={lead}
          linkTo={linkTo}
          linkLabel={linkLabel}
          light
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

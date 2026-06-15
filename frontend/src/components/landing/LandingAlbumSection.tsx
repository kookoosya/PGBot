import type { ReactNode } from "react";

interface LandingAlbumSectionProps {
  children: ReactNode;
  className?: string;
  /** Декоративный разделитель сверху */
  divider?: boolean;
  id?: string;
}

/** Обёртка секции главной — единый ритм и отступы альбома */
export function LandingAlbumSection({ children, className = "", divider = false, id }: LandingAlbumSectionProps) {
  return (
    <section id={id} className={`landing-album-section ${divider ? "landing-album-section--divider" : ""} ${className}`.trim()}>
      {children}
    </section>
  );
}

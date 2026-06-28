import type { ReactNode } from "react";
import { useRevealOnScroll } from "@/hooks/useRevealOnScroll";

interface LandingAlbumSectionProps {
  children: ReactNode;
  className?: string;
  /** Декоративный разделитель сверху */
  divider?: boolean;
  id?: string;
  /** Плавное появление при скролле */
  reveal?: boolean;
}

/** Обёртка секции главной — единый ритм и отступы альбома */
export function LandingAlbumSection({
  children,
  className = "",
  divider = false,
  id,
  reveal = false,
}: LandingAlbumSectionProps) {
  const { ref, visible } = useRevealOnScroll<HTMLElement>();

  return (
    <section
      id={id}
      ref={reveal ? ref : undefined}
      className={[
        "landing-album-section",
        divider ? "landing-album-section--divider" : "",
        reveal ? "landing-reveal" : "",
        reveal && visible ? "landing-reveal--visible" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {children}
    </section>
  );
}

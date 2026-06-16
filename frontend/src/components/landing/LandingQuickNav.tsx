import { LiterarySectionHead } from "@/components/literary";
import { LANDING_SECTIONS } from "@/lib/literaryCopy";
import { PortalNavGrid } from "@/components/layout/PortalNavGrid";

/** Компактная навигация по разделам — для главной. */
export function LandingQuickNav() {
  const copy = LANDING_SECTIONS.useful;

  return (
    <nav className="page-panel page-panel--gold landing-block" aria-label="Разделы портала">
      <LiterarySectionHead kicker={copy.kicker} title={copy.title} compact />
      <PortalNavGrid />
    </nav>
  );
}
